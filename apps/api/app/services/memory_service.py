import re
import uuid
from datetime import datetime
from typing import List, Optional

from app.db.database import db
from app.models.schemas import (
    Task,
    UserMemoryCreate,
    UserMemoryItem,
    UserMemoryUpdate,
    UserPlanningContext,
    UserPreferences,
    UserPreferencesUpdate,
    MemorySourceType,
)


class MemoryService:
    @staticmethod
    def get_preferences(user_id: str = "default") -> UserPreferences:
        preferences = db.get_user_preferences(user_id)
        if preferences:
            return preferences

        preferences = UserPreferences(user_id=user_id, updated_at=datetime.now())
        return db.upsert_user_preferences(preferences)

    @staticmethod
    def update_preferences(
        payload: UserPreferencesUpdate,
        user_id: str = "default",
    ) -> UserPreferences:
        current_preferences = MemoryService.get_preferences(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        merged = current_preferences.model_copy(
            update={**update_data, "updated_at": datetime.now()}
        )
        return db.upsert_user_preferences(merged)

    @staticmethod
    def list_memories(
        user_id: str = "default",
        category: Optional[str] = None,
    ) -> List[UserMemoryItem]:
        return db.list_user_memories(user_id=user_id, category=category)

    @staticmethod
    def create_memory(
        payload: UserMemoryCreate,
        user_id: str = "default",
    ) -> UserMemoryItem:
        existing_memory = MemoryService._find_memory_by_content(
            user_id=user_id,
            content=payload.content,
            category=payload.category,
        )
        if existing_memory:
            merged_tags = sorted(set(existing_memory.tags + payload.tags))
            refreshed_memory = existing_memory.model_copy(
                update={
                    "source": payload.source,
                    "tags": merged_tags,
                    "updated_at": datetime.now(),
                }
            )
            return db.update_user_memory(refreshed_memory) or refreshed_memory

        now = datetime.now()
        memory = UserMemoryItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category=payload.category,
            source=payload.source,
            content=payload.content,
            tags=payload.tags,
            source_confidence=payload.source_confidence,
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
            last_used_at=None,
        )
        return db.create_user_memory(memory)

    @staticmethod
    def update_memory(
        memory_id: str,
        payload: UserMemoryUpdate,
        user_id: str = "default",
    ) -> UserMemoryItem | None:
        existing = next(
            (memory for memory in db.list_user_memories(user_id=user_id) if memory.id == memory_id),
            None,
        )
        if not existing:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        if "source" not in update_data:
            update_data["source"] = MemorySourceType.USER_EDITED
        update_data["updated_at"] = datetime.now()
        updated_memory = existing.model_copy(update=update_data)
        return db.update_user_memory(updated_memory)

    @staticmethod
    def delete_memory(memory_id: str) -> bool:
        return db.delete_user_memory(memory_id)

    @staticmethod
    def build_planning_context(
        prompt: str,
        user_id: str = "default",
    ) -> UserPlanningContext:
        preferences = MemoryService.get_preferences(user_id)
        relevant_memories = MemoryService._select_relevant_memories(
            prompt=prompt,
            user_id=user_id,
        )
        behavior_summary = MemoryService._build_behavior_summary()
        prompt_context = MemoryService._compose_prompt_context(
            preferences=preferences,
            relevant_memories=relevant_memories,
            behavior_summary=behavior_summary,
        )

        for memory in relevant_memories:
            db.update_user_memory(
                memory.model_copy(
                    update={
                        "last_used_at": datetime.now(),
                        "relevance_score": round(
                            max(memory.relevance_score or 0.5, 0.5),
                            2,
                        ),
                    }
                )
            )

        return UserPlanningContext(
            preferences=preferences,
            relevant_memories=relevant_memories,
            behavior_summary=behavior_summary,
            prompt_context=prompt_context,
        )

    @staticmethod
    def observe_task_patterns(
        task: Task,
        previous_task: Optional[Task] = None,
        user_id: str = "default",
    ) -> None:
        MemoryService._apply_duration_preference(task=task, user_id=user_id)

        for extracted_memory in MemoryService._extract_memories_from_task(task):
            if previous_task and extracted_memory.content in [
                previous_task.name or "",
                previous_task.description or "",
            ]:
                continue
            MemoryService.create_memory(extracted_memory, user_id=user_id)

    @staticmethod
    def _apply_duration_preference(task: Task, user_id: str) -> None:
        if not task.estimated_hours:
            return

        preferences = MemoryService.get_preferences(user_id)
        smoothed_duration = round(
            preferences.preferred_task_duration_hours * 0.7 + float(task.estimated_hours) * 0.3,
            1,
        )
        if abs(smoothed_duration - preferences.preferred_task_duration_hours) < 0.2:
            return

        updated_preferences = preferences.model_copy(
            update={
                "preferred_task_duration_hours": smoothed_duration,
                "updated_at": datetime.now(),
            }
        )
        db.upsert_user_preferences(updated_preferences)

    @staticmethod
    def _extract_memories_from_task(task: Task) -> List[UserMemoryCreate]:
        text_blocks = [task.name or "", task.description or ""]
        extracted: List[UserMemoryCreate] = []

        for text in text_blocks:
            if not text:
                continue

            lower_text = text.lower()
            if any(keyword in lower_text for keyword in ["focus on", "prioritize", "goal", "career"]):
                extracted.append(
                    UserMemoryCreate(
                        category="goal",
                        source=MemorySourceType.SYSTEM_INFERRED,
                        content=text.strip(),
                        tags=["task-derived", "goal"],
                        source_confidence=0.72,
                    )
                )

            if any(keyword in lower_text for keyword in ["avoid", "before", "after", "not during", "不要", "避免", "之前"]):
                extracted.append(
                    UserMemoryCreate(
                        category="constraint",
                        source=MemorySourceType.SYSTEM_INFERRED,
                        content=text.strip(),
                        tags=["task-derived", "constraint"],
                        source_confidence=0.68,
                    )
                )

            if any(keyword in lower_text for keyword in ["prefer", "usually", "习惯", "偏好"]):
                extracted.append(
                    UserMemoryCreate(
                        category="preference",
                        source=MemorySourceType.SYSTEM_INFERRED,
                        content=text.strip(),
                        tags=["task-derived", "preference"],
                        source_confidence=0.66,
                    )
                )

        deduped = {}
        for memory in extracted:
            deduped[(memory.category, memory.content.strip().lower())] = memory
        return list(deduped.values())

    @staticmethod
    def _find_memory_by_content(
        *,
        user_id: str,
        content: str,
        category: str,
    ) -> Optional[UserMemoryItem]:
        normalized_content = content.strip().lower()
        for memory in db.list_user_memories(user_id=user_id):
            if memory.category == category and memory.content.strip().lower() == normalized_content:
                return memory
        return None

    @staticmethod
    def _select_relevant_memories(
        *,
        prompt: str,
        user_id: str,
        limit: int = 5,
    ) -> List[UserMemoryItem]:
        memories = db.list_user_memories(user_id=user_id)
        if not memories:
            return []

        normalized_prompt = prompt.lower()
        tokens = {
            token
            for token in re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", normalized_prompt)
            if len(token) >= 2
        }

        scored_memories = []
        for memory in memories:
            searchable_text = " ".join(
                [memory.content.lower(), " ".join(tag.lower() for tag in memory.tags)]
            )
            score = 0
            for token in tokens:
                if token in searchable_text:
                    score += 1
            if memory.category in {"goal", "constraint", "preference"}:
                score += 1
            scored_memories.append((score, memory))

        scored_memories.sort(
            key=lambda item: (
                item[0],
                item[1].updated_at or item[1].created_at or datetime.min,
            ),
            reverse=True,
        )

        top_memories = []
        for score, memory in scored_memories:
            if score <= 0:
                continue
            top_memories.append(
                memory.model_copy(
                    update={
                        "relevance_score": min(1.0, round(score / max(len(tokens), 1), 2)),
                    }
                )
            )
            if len(top_memories) >= limit:
                break
        if top_memories:
            return top_memories
        return [
            memory.model_copy(update={"relevance_score": 0.2})
            for memory in memories[: min(limit, 3)]
        ]

    @staticmethod
    def _build_behavior_summary() -> str:
        tasks = db.get_all_tasks()
        pending_tasks = [task for task in tasks if not task.completed]
        overdue_tasks = [
            task
            for task in pending_tasks
            if task.due_date and task.due_date.date() < datetime.now().date()
        ]
        open_task_hours = [
            task.estimated_hours for task in pending_tasks if task.estimated_hours
        ]
        average_open_task_hours = (
            round(sum(open_task_hours) / len(open_task_hours), 1) if open_task_hours else 0.0
        )
        high_priority_pending = sum(1 for task in pending_tasks if task.priority == "high")

        return (
            f"The user currently has {len(pending_tasks)} pending tasks, "
            f"{len(overdue_tasks)} overdue tasks, and an average open-task estimate of "
            f"{average_open_task_hours} hours. High-priority open tasks: {high_priority_pending}."
        )

    @staticmethod
    def _compose_prompt_context(
        *,
        preferences: UserPreferences,
        relevant_memories: List[UserMemoryItem],
        behavior_summary: str,
    ) -> str:
        preference_lines = [
            f"Work hours: {preferences.work_start_time}-{preferences.work_end_time}",
            f"Peak focus period: {preferences.peak_focus_period}",
            f"Planning style: {preferences.planning_style}",
            f"Priority preference: {preferences.priority_preference}",
            f"Preferred task duration: {preferences.preferred_task_duration_hours} hours",
            f"Max daily focus hours: {preferences.max_daily_focus_hours}",
            f"Break interval: {preferences.break_interval_minutes} minutes",
        ]
        if preferences.avoid_time_ranges:
            preference_lines.append(
                "Avoid time ranges: " + ", ".join(preferences.avoid_time_ranges)
            )

        memory_lines = [
            f"- [{memory.category}] {memory.content}"
            for memory in relevant_memories
        ]
        if not memory_lines:
            memory_lines.append("- No explicit long-term memories recorded yet.")

        return "\n".join(
            [
                "User preferences:",
                *preference_lines,
                "",
                "Relevant long-term memory:",
                *memory_lines,
                "",
                "Observed task behavior:",
                behavior_summary,
            ]
        )
