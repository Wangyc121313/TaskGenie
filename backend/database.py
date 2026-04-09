"""
数据库操作模块 - SQLAlchemy + SQLite 持久化版本
数据存储在 taskgenie.db 文件中，服务重启后数据不会丢失
"""
import json
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import create_engine, Column, String, Boolean, Float, DateTime, Date, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from models import Task, AIJob, AIJobStatus, DaySchedule, TaskStatus

# ===== SQLAlchemy 配置 =====
DATABASE_URL = "sqlite:///./taskgenie.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

# ===== ORM 模型 =====
class TaskORM(Base):
    __tablename__ = "tasks"
    id            = Column(String, primary_key=True)
    name          = Column(String, nullable=False)
    description   = Column(Text, default="")
    completed     = Column(Boolean, default=False)
    status        = Column(String, default="pending")
    created_at    = Column(DateTime)
    due_date      = Column(DateTime, nullable=True)
    priority      = Column(String, default="medium")
    estimated_hours = Column(Float, nullable=True)
    scheduled_date  = Column(Date, nullable=True)

class AIJobORM(Base):
    __tablename__ = "ai_jobs"
    job_id     = Column(String, primary_key=True)
    status     = Column(String, default="pending")
    created_at = Column(DateTime)
    result     = Column(Text, nullable=True)   # JSON string
    error      = Column(Text, nullable=True)

class DayScheduleORM(Base):
    __tablename__ = "day_schedules"
    date_str = Column(String, primary_key=True)  # YYYY-MM-DD
    data     = Column(Text, nullable=False)       # full JSON of DaySchedule

# 建表（首次运行时自动创建）
Base.metadata.create_all(bind=engine)


# ===== 转换工具 =====
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
    result = json.loads(row.result) if row.result else None
    return AIJob(
        job_id=row.job_id,
        status=AIJobStatus(row.status),
        created_at=row.created_at,
        result=result,
        error=row.error,
    )


# ===== 数据库操作类（保持与原 InMemoryDatabase 完全相同的接口）=====
class SQLiteDatabase:

    def _get_session(self) -> Session:
        return SessionLocal()

    # ===== 任务操作 =====
    def create_task(self, task: Task) -> Task:
        with self._get_session() as session:
            row = TaskORM(
                id=task.id,
                name=task.name,
                description=task.description or "",
                completed=task.completed,
                status=task.status.value if hasattr(task.status, 'value') else task.status,
                created_at=task.created_at,
                due_date=task.due_date,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                scheduled_date=task.scheduled_date,
            )
            session.add(row)
            session.commit()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._get_session() as session:
            row = session.get(TaskORM, task_id)
            return _task_orm_to_pydantic(row) if row else None

    def get_all_tasks(self) -> List[Task]:
        with self._get_session() as session:
            rows = session.query(TaskORM).order_by(TaskORM.created_at.desc()).all()
            return [_task_orm_to_pydantic(r) for r in rows]

    def update_task(self, task_id: str, task: Task) -> Optional[Task]:
        with self._get_session() as session:
            row = session.get(TaskORM, task_id)
            if not row:
                return None
            row.name            = task.name
            row.description     = task.description or ""
            row.completed       = task.completed
            row.status          = task.status.value if hasattr(task.status, 'value') else task.status
            row.due_date        = task.due_date
            row.priority        = task.priority
            row.estimated_hours = task.estimated_hours
            row.scheduled_date  = task.scheduled_date
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
        all_tasks = self.get_all_tasks()
        result = []
        for task in all_tasks:
            if task.completed:
                continue
            if (task.due_date and task.due_date.date() == target_date) or \
               (task.scheduled_date and task.scheduled_date == target_date):
                result.append(task)
        return result

    # ===== AI 作业操作 =====
    def create_ai_job(self, job: AIJob) -> AIJob:
        with self._get_session() as session:
            row = AIJobORM(
                job_id=job.job_id,
                status=job.status.value if hasattr(job.status, 'value') else job.status,
                created_at=job.created_at,
                result=json.dumps(job.result, default=str) if job.result is not None else None,
                error=job.error,
            )
            session.add(row)
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
            row.status = job.status.value if hasattr(job.status, 'value') else job.status
            row.result = json.dumps(job.result, default=str) if job.result is not None else None
            row.error  = job.error
            session.commit()
        return job

    # ===== 日程安排操作 =====
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

    def clear_all(self):
        """清空所有数据 - 仅供测试使用"""
        with self._get_session() as session:
            session.query(TaskORM).delete()
            session.query(AIJobORM).delete()
            session.query(DayScheduleORM).delete()
            session.commit()


# 全局数据库实例
db = SQLiteDatabase()