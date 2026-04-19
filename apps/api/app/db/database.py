import json
from datetime import date
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import current_settings
from app.models.schemas import (
    AIJob,
    AIJobStatus,
    ConversationSession,
    DaySchedule,
    Task,
    TaskStatus,
    UserMemoryItem,
    UserPreferences,
)


DEFAULT_SQLITE_DATABASE_URL = "sqlite:///./taskgenie.db"


def resolve_database_url(database_url: Optional[str]) -> str:
    return database_url or DEFAULT_SQLITE_DATABASE_URL


def build_engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


DATABASE_URL = resolve_database_url(current_settings.DATABASE_URL)
engine = create_engine(DATABASE_URL, **build_engine_options(DATABASE_URL))
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class TaskORM(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    completed = Column(Boolean, default=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, default="medium")
    estimated_hours = Column(Float, nullable=True)
    scheduled_date = Column(Date, nullable=True)


class AIJobORM(Base):
    __tablename__ = "ai_jobs"

    job_id = Column(String, primary_key=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    trace = Column(Text, nullable=True)


class DayScheduleORM(Base):
    __tablename__ = "day_schedules"

    date_str = Column(String, primary_key=True)
    data = Column(Text, nullable=False)


class UserPreferenceORM(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String, primary_key=True)
    data = Column(Text, nullable=False)


class UserMemoryORM(Base):
    __tablename__ = "user_memories"

    memory_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime, nullable=False)
    data = Column(Text, nullable=False)


class ConversationSessionORM(Base):
    __tablename__ = "conversation_sessions"

    conversation_id = Column(String, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    data = Column(Text, nullable=False)


Base.metadata.create_all(bind=engine)


def _ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    ai_job_columns = {column["name"] for column in inspector.get_columns("ai_jobs")}
    if "trace" not in ai_job_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE ai_jobs ADD COLUMN trace TEXT"))


_ensure_schema_compatibility()


def _task_orm_to_pydantic(row: TaskORM) -> Task:
    return Task(
        id=row.id,
        name=row.name,
        description=row.description or "",
        completed=row.completed,
        status=TaskStatus(row.status),
        created_at=row.created_at,
        due_date=row.due_date,
        priority=row.priority,
        estimated_hours=row.estimated_hours,
        scheduled_date=row.scheduled_date,
    )


def _aijob_orm_to_pydantic(row: AIJobORM) -> AIJob:
    return AIJob(
        job_id=row.job_id,
        status=AIJobStatus(row.status),
        created_at=row.created_at,
        result=json.loads(row.result) if row.result else None,
        error=row.error,
        trace=json.loads(row.trace) if row.trace else None,
    )


def _preferences_orm_to_pydantic(row: UserPreferenceORM) -> UserPreferences:
    return UserPreferences.model_validate_json(row.data)


def _memory_orm_to_pydantic(row: UserMemoryORM) -> UserMemoryItem:
    return UserMemoryItem.model_validate_json(row.data)


def _conversation_orm_to_pydantic(row: ConversationSessionORM) -> ConversationSession:
    return ConversationSession.model_validate_json(row.data)


class SQLiteDatabase:
    def _get_session(self) -> Session:
        return SessionLocal()

    def create_task(self, task: Task) -> Task:
        with self._get_session() as session:
            session.add(
                TaskORM(
                    id=task.id,
                    name=task.name,
                    description=task.description or "",
                    completed=task.completed,
                    status=task.status.value if hasattr(task.status, "value") else task.status,
                    created_at=task.created_at,
                    due_date=task.due_date,
                    priority=task.priority,
                    estimated_hours=task.estimated_hours,
                    scheduled_date=task.scheduled_date,
                )
            )
            session.commit()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._get_session() as session:
            row = session.get(TaskORM, task_id)
            return _task_orm_to_pydantic(row) if row else None

    def get_all_tasks(self) -> List[Task]:
        with self._get_session() as session:
            rows = session.query(TaskORM).order_by(TaskORM.created_at.desc()).all()
            return [_task_orm_to_pydantic(row) for row in rows]

    def update_task(self, task_id: str, task: Task) -> Optional[Task]:
        with self._get_session() as session:
            row = session.get(TaskORM, task_id)
            if not row:
                return None
            row.name = task.name
            row.description = task.description or ""
            row.completed = task.completed
            row.status = task.status.value if hasattr(task.status, "value") else task.status
            row.due_date = task.due_date
            row.priority = task.priority
            row.estimated_hours = task.estimated_hours
            row.scheduled_date = task.scheduled_date
            session.commit()
        return task

    def delete_task(self, task_id: str) -> bool:
        with self._get_session() as session:
            row = session.get(TaskORM, task_id)
            if not row:
                return False
            session.delete(row)
            session.commit()
        return True

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        result: List[Task] = []
        for task in self.get_all_tasks():
            if task.completed:
                continue
            if (task.due_date and task.due_date.date() == target_date) or (
                task.scheduled_date and task.scheduled_date == target_date
            ):
                result.append(task)
        return result

    def create_ai_job(self, job: AIJob) -> AIJob:
        with self._get_session() as session:
            session.add(
                AIJobORM(
                    job_id=job.job_id,
                    status=job.status.value if hasattr(job.status, "value") else job.status,
                    created_at=job.created_at,
                    result=json.dumps(job.result, default=str) if job.result is not None else None,
                    error=job.error,
                    trace=job.trace.model_dump_json() if job.trace is not None else None,
                )
            )
            session.commit()
        return job

    def get_ai_job(self, job_id: str) -> Optional[AIJob]:
        with self._get_session() as session:
            row = session.get(AIJobORM, job_id)
            return _aijob_orm_to_pydantic(row) if row else None

    def update_ai_job(self, job_id: str, job: AIJob) -> Optional[AIJob]:
        with self._get_session() as session:
            row = session.get(AIJobORM, job_id)
            if not row:
                return None
            row.status = job.status.value if hasattr(job.status, "value") else job.status
            row.result = json.dumps(job.result, default=str) if job.result is not None else None
            row.error = job.error
            row.trace = job.trace.model_dump_json() if job.trace is not None else None
            session.commit()
        return job

    def create_day_schedule(self, date_str: str, schedule: DaySchedule) -> DaySchedule:
        with self._get_session() as session:
            existing = session.get(DayScheduleORM, date_str)
            data_json = schedule.model_dump_json()
            if existing:
                existing.data = data_json
            else:
                session.add(DayScheduleORM(date_str=date_str, data=data_json))
            session.commit()
        return schedule

    def get_day_schedule(self, date_str: str) -> Optional[DaySchedule]:
        with self._get_session() as session:
            row = session.get(DayScheduleORM, date_str)
            if not row:
                return None
            return DaySchedule.model_validate_json(row.data)

    def delete_day_schedule(self, date_str: str) -> bool:
        with self._get_session() as session:
            row = session.get(DayScheduleORM, date_str)
            if not row:
                return False
            session.delete(row)
            session.commit()
        return True

    def get_user_preferences(self, user_id: str = "default") -> Optional[UserPreferences]:
        with self._get_session() as session:
            row = session.get(UserPreferenceORM, user_id)
            return _preferences_orm_to_pydantic(row) if row else None

    def upsert_user_preferences(self, preferences: UserPreferences) -> UserPreferences:
        with self._get_session() as session:
            row = session.get(UserPreferenceORM, preferences.user_id)
            data_json = preferences.model_dump_json()
            if row:
                row.data = data_json
            else:
                session.add(UserPreferenceORM(user_id=preferences.user_id, data=data_json))
            session.commit()
        return preferences

    def create_user_memory(self, memory: UserMemoryItem) -> UserMemoryItem:
        with self._get_session() as session:
            session.add(
                UserMemoryORM(
                    memory_id=memory.id,
                    user_id=memory.user_id,
                    created_at=memory.created_at,
                    data=memory.model_dump_json(),
                )
            )
            session.commit()
        return memory

    def list_user_memories(
        self,
        user_id: str = "default",
        category: Optional[str] = None,
    ) -> List[UserMemoryItem]:
        with self._get_session() as session:
            rows = (
                session.query(UserMemoryORM)
                .filter(UserMemoryORM.user_id == user_id)
                .order_by(UserMemoryORM.created_at.desc())
                .all()
            )
            memories = [_memory_orm_to_pydantic(row) for row in rows]
            if category:
                memories = [memory for memory in memories if memory.category == category]
            return memories

    def update_user_memory(self, memory: UserMemoryItem) -> Optional[UserMemoryItem]:
        with self._get_session() as session:
            row = session.get(UserMemoryORM, memory.id)
            if not row:
                return None
            row.user_id = memory.user_id
            row.created_at = memory.created_at
            row.data = memory.model_dump_json()
            session.commit()
        return memory

    def delete_user_memory(self, memory_id: str) -> bool:
        with self._get_session() as session:
            row = session.get(UserMemoryORM, memory_id)
            if not row:
                return False
            session.delete(row)
            session.commit()
        return True

    def get_conversation(self, conversation_id: str) -> Optional[ConversationSession]:
        with self._get_session() as session:
            row = session.get(ConversationSessionORM, conversation_id)
            return _conversation_orm_to_pydantic(row) if row else None

    def upsert_conversation(self, conversation: ConversationSession) -> ConversationSession:
        with self._get_session() as session:
            row = session.get(ConversationSessionORM, conversation.conversation_id)
            data_json = conversation.model_dump_json()
            if row:
                row.updated_at = conversation.updated_at
                row.data = data_json
            else:
                session.add(
                    ConversationSessionORM(
                        conversation_id=conversation.conversation_id,
                        created_at=conversation.created_at,
                        updated_at=conversation.updated_at,
                        data=data_json,
                    )
                )
            session.commit()
        return conversation

    def clear_all(self):
        with self._get_session() as session:
            session.query(TaskORM).delete()
            session.query(AIJobORM).delete()
            session.query(DayScheduleORM).delete()
            session.query(UserPreferenceORM).delete()
            session.query(UserMemoryORM).delete()
            session.query(ConversationSessionORM).delete()
            session.commit()


db = SQLiteDatabase()
