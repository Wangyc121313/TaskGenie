import re
import uuid
from datetime import datetime
from typing import List, Optional

from app.db.database import db
from app.models.schemas import (
    UserMemoryCreate,
    UserMemoryItem,
    UserPlanningContext,
    UserPreferences,
    UserPreferencesUpdate,
)
from app.services.task_service import TaskService


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
        now = datetime.now()
        memory = UserMemoryItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category=payload.category,
            source=payload.source,
            content=payload.content,
            tags=payload.tags,
            created_at=now,
            updated_at=now,
            last_used_at=None,
        )
        return db.create_user_memory(memory)

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
            if memory.last_used_at is None:
                updated_memory = memory.model_copy(update={"last_used_at": datetime.now()})
                db.update_user_memory(updated_memory)
            else:
                updated_memory = memory.model_copy(update={"last_used_at": datetime.now()})
                db.update_user_memory(updated_memory)

        return UserPlanningContext(
            preferences=preferences,
            relevant_memories=relevant_memories,
            behavior_summary=behavior_summary,
            prompt_context=prompt_context,
        )

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
            searchable_text = " ".join([memory.content.lower(), " ".join(tag.lower() for tag in memory.tags)])
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

        top_memories = [memory for score, memory in scored_memories if score > 0][:limit]
        if top_memories:
            return top_memories
        return memories[: min(limit, 3)]

    @staticmethod
    def _build_behavior_summary() -> str:
        stats = TaskService.get_task_stats()
        tasks = TaskService.get_all_tasks()
        open_task_hours = [task.estimated_hours for task in tasks if not task.completed and task.estimated_hours]
        average_open_task_hours = (
            round(sum(open_task_hours) / len(open_task_hours), 1) if open_task_hours else 0.0
        )

        return (
            f"The user currently has {stats['pending']} pending tasks, "
            f"{stats['overdue']} overdue tasks, and an average open-task estimate of "
            f"{average_open_task_hours} hours. High-priority open tasks: {stats['by_priority']['high']}."
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
