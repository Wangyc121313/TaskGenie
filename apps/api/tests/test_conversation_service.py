from datetime import datetime

from app.db.database import db
from app.models.schemas import ConversationTurnStatus
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService


def setup_function():
    db.clear_all()


def test_conversation_service_compacts_running_summary_with_llm(monkeypatch):
    compressed_calls = []

    def fake_compress_running_summary(*, title, existing_summary, recent_turns):
        compressed_calls.append(
            {
                "title": title,
                "existing_summary": existing_summary,
                "recent_turns": recent_turns,
            }
        )
        return "Compressed: user is preparing an AI agent launch and already created follow-up tasks."

    monkeypatch.setattr(LLMService, "compress_running_summary", fake_compress_running_summary)

    session = ConversationService.get_or_create_conversation(
        None,
        initial_prompt="Prepare the AI agent launch plan",
    )

    for index in range(6):
        session = ConversationService.upsert_turn(
            conversation_id=session.conversation_id,
            job_id=f"job-{index}",
            user_message=f"Turn {index} about launch preparation and interview readiness",
            goal_summary=f"Goal summary {index}",
            agent_summary=f"Agent completed turn {index} with a detailed result summary",
            status=ConversationTurnStatus.COMPLETED,
            created_task_count=1,
        )

    assert compressed_calls
    assert session.running_summary.startswith("Compressed:")
    context = ConversationService.build_context(session)
    assert "Compressed:" in context

