import uuid
from datetime import datetime
from typing import Optional

from app.db.database import db
from app.models.schemas import ConversationSession, ConversationTurn, ConversationTurnStatus


class ConversationService:
    @staticmethod
    def get_or_create_conversation(
        conversation_id: Optional[str],
        *,
        initial_prompt: str,
    ) -> ConversationSession:
        if conversation_id:
            existing = db.get_conversation(conversation_id)
            if existing:
                return existing

        now = datetime.now()
        created = ConversationSession(
            conversation_id=conversation_id or str(uuid.uuid4()),
            title=ConversationService._build_title(initial_prompt),
            running_summary="",
            turn_count=0,
            turns=[],
            created_at=now,
            updated_at=now,
        )
        return db.upsert_conversation(created)

    @staticmethod
    def get_conversation(conversation_id: str) -> Optional[ConversationSession]:
        return db.get_conversation(conversation_id)

    @staticmethod
    def build_context(session: ConversationSession, *, max_turns: int = 3) -> str:
        if not session.turns:
            return ""

        recent_turns = session.turns[-max_turns:]
        lines = ["Conversation summary:"]
        if session.running_summary:
            lines.append(session.running_summary)
        lines.append("Recent turns:")
        for turn in recent_turns:
            lines.append(f"- User: {turn.user_message}")
            if turn.agent_summary:
                lines.append(f"  Agent: {turn.agent_summary}")
        return "\n".join(lines)

    @staticmethod
    def upsert_turn(
        *,
        conversation_id: str,
        job_id: str,
        user_message: str,
        goal_summary: Optional[str],
        agent_summary: str,
        status: ConversationTurnStatus,
        created_task_count: int,
    ) -> ConversationSession:
        session = db.get_conversation(conversation_id)
        if not session:
            session = ConversationService.get_or_create_conversation(
                conversation_id,
                initial_prompt=user_message,
            )

        turn = next((item for item in session.turns if item.job_id == job_id), None)
        if turn is None:
            turn = ConversationTurn(
                turn_id=str(uuid.uuid4()),
                job_id=job_id,
                user_message=user_message,
                goal_summary=goal_summary,
                agent_summary=agent_summary,
                status=status,
                created_task_count=created_task_count,
                created_at=datetime.now(),
            )
            session.turns.append(turn)
        else:
            turn.goal_summary = goal_summary
            turn.agent_summary = agent_summary
            turn.status = status
            turn.created_task_count = created_task_count

        session.updated_at = datetime.now()
        session.turn_count = len(session.turns)
        session.running_summary = ConversationService._compose_running_summary(session)
        return db.upsert_conversation(session)

    @staticmethod
    def _compose_running_summary(session: ConversationSession, *, max_turns: int = 5) -> str:
        recent_turns = session.turns[-max_turns:]
        if not recent_turns:
            return ""

        summary_lines = []
        for turn in recent_turns:
            outcome = turn.agent_summary or turn.goal_summary or "No summary available."
            summary_lines.append(
                f"User asked: {turn.user_message} | Outcome: {outcome} | Status: {turn.status.value}"
            )
        return "\n".join(summary_lines)

    @staticmethod
    def _build_title(prompt: str) -> str:
        normalized = " ".join(prompt.strip().split())
        if len(normalized) <= 48:
            return normalized or "Conversation"
        return f"{normalized[:45]}..."
