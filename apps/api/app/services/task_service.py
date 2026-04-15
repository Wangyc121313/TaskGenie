import uuid
from datetime import date, datetime
from typing import List, Optional

from app.db.database import db
from app.models.schemas import Task, TaskCreate, TaskStatus, TaskUpdate
from app.services.memory_service import MemoryService
from app.services.tag_service import TagService


class TaskService:
    @staticmethod
    def create_task(task_data: TaskCreate) -> Task:
        completed = task_data.completed or False
        new_task = Task(
            id=str(uuid.uuid4()),
            name=task_data.name,
            description=task_data.description,
            completed=completed,
            status=TaskStatus.COMPLETED if completed else TaskStatus.PENDING,
            created_at=datetime.now(),
            due_date=task_data.due_date,
            priority=task_data.priority,
            estimated_hours=task_data.estimated_hours,
            scheduled_date=task_data.scheduled_date,
        )

        created_task = db.create_task(new_task)
        MemoryService.observe_task_patterns(created_task)
        return created_task

    @staticmethod
    def get_task(task_id: str) -> Optional[Task]:
        return db.get_task(task_id)

    @staticmethod
    def get_all_tasks() -> List[Task]:
        return db.get_all_tasks()

    @staticmethod
    def get_tasks_by_tags(tags: List[str]) -> List[Task]:
        return TagService.get_tasks_by_tags(db.get_all_tasks(), tags)

    @staticmethod
    def get_tasks_by_tag(tag: str) -> List[Task]:
        return TagService.get_tasks_by_tag(db.get_all_tasks(), tag)

    @staticmethod
    def update_task(task_id: str, task_update: TaskUpdate) -> Optional[Task]:
        task = db.get_task(task_id)
        if not task:
            return None

        previous_task = task.model_copy(deep=True)
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.status = TaskStatus.COMPLETED if task.completed else TaskStatus.PENDING
        updated_task = db.update_task(task_id, task)
        if updated_task:
            MemoryService.observe_task_patterns(updated_task, previous_task=previous_task)
        return updated_task

    @staticmethod
    def delete_task(task_id: str) -> bool:
        return db.delete_task(task_id)

    @staticmethod
    def get_calendar_tasks(year: int, month: int) -> dict:
        calendar_data = {}
        tasks = db.get_all_tasks()

        for task in tasks:
            if task.completed:
                continue

            if task.due_date:
                due_day = task.due_date.date()
                if due_day.year == year and due_day.month == month:
                    date_str = due_day.isoformat()
                    if date_str not in calendar_data:
                        calendar_data[date_str] = {"due": [], "scheduled": []}
                    calendar_data[date_str]["due"].append(task)

            if task.scheduled_date:
                if task.scheduled_date.year == year and task.scheduled_date.month == month:
                    date_str = task.scheduled_date.isoformat()
                    if date_str not in calendar_data:
                        calendar_data[date_str] = {"due": [], "scheduled": []}
                    calendar_data[date_str]["scheduled"].append(task)

        return calendar_data

    @staticmethod
    def get_task_stats() -> dict:
        tasks = db.get_all_tasks()
        completed = sum(1 for task in tasks if task.completed)
        today = date.today()
        due_today = sum(
            1
            for task in tasks
            if task.due_date and task.due_date.date() == today and not task.completed
        )
        overdue = sum(
            1
            for task in tasks
            if task.due_date and task.due_date.date() < today and not task.completed
        )

        return {
            "total": len(tasks),
            "completed": completed,
            "pending": len(tasks) - completed,
            "due_today": due_today,
            "overdue": overdue,
            "by_priority": {
                "high": sum(1 for task in tasks if task.priority == "high" and not task.completed),
                "medium": sum(1 for task in tasks if task.priority == "medium" and not task.completed),
                "low": sum(1 for task in tasks if task.priority == "low" and not task.completed),
            },
            "by_status": {
                "pending": sum(1 for task in tasks if task.status == TaskStatus.PENDING),
                "in_progress": sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS),
                "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
            },
            "by_tags": TagService.get_tag_stats(tasks),
        }
