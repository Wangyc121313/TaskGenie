from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AIJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    completed: bool = False
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: Literal["low", "medium", "high"] = "medium"
    estimated_hours: Optional[float] = None
    scheduled_date: Optional[date] = None


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    completed: Optional[bool] = False
    due_date: Optional[datetime] = None
    priority: Literal["low", "medium", "high"] = "medium"
    estimated_hours: Optional[float] = None
    scheduled_date: Optional[date] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    estimated_hours: Optional[float] = None
    scheduled_date: Optional[date] = None


class AITaskRequest(BaseModel):
    prompt: str
    max_tasks: int = 5


class AIScheduleRequest(BaseModel):
    task_ids: Optional[List[str]] = None


class AIDayScheduleRequest(BaseModel):
    date: str
    task_ids: Optional[List[str]] = None


class PlannedTask(BaseModel):
    name: str
    description: str
    priority: Literal["low", "medium", "high"] = "medium"
    estimated_hours: float = 2.0
    due_date: Optional[datetime] = None


class TaskPlanningResult(BaseModel):
    project_theme: str
    tasks: List[PlannedTask]


class PlannedScheduleItem(BaseModel):
    task_id: str
    start_time: str
    end_time: str
    reason: str


class DayScheduleGenerationResult(BaseModel):
    schedule: List[PlannedScheduleItem]
    suggestions: List[str] = []
    efficiency_score: int = 8


class TaskScheduleItem(BaseModel):
    task_id: str
    task_name: str
    start_time: str
    end_time: str
    duration: float
    priority: str
    reason: str


class DaySchedule(BaseModel):
    id: Optional[str] = None
    date: date
    created_at: datetime
    updated_at: datetime
    schedule_items: List[TaskScheduleItem]
    suggestions: List[str]
    total_hours: float
    efficiency_score: int
    task_version: str


class DayScheduleResponse(BaseModel):
    date: str
    has_schedule: bool
    schedule: Optional[DaySchedule] = None
    tasks_changed: bool = False


class AIJob(BaseModel):
    job_id: str
    status: AIJobStatus
    created_at: datetime
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskStatsResponse(BaseModel):
    total: int
    completed: int
    pending: int
    due_today: int
    overdue: int
    by_priority: Dict[str, int]
    by_status: Dict[str, int]
    by_tags: Dict[str, int]


class TagsResponse(BaseModel):
    system_tags: List[str]
    tag_descriptions: Dict[str, str]
