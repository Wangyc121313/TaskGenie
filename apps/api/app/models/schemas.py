from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AIJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentExecutionStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
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


class AIImageTaskRequest(BaseModel):
    image_base64: str
    image_mime_type: str = "image/png"
    filename: Optional[str] = "upload-image"
    notes: str = ""
    max_tasks: int = 5
    auto_create: bool = False


class PlannedTask(BaseModel):
    name: str
    description: str
    priority: Literal["low", "medium", "high"] = "medium"
    estimated_hours: float = 2.0
    due_date: Optional[datetime] = None


class ImageTaskCandidate(PlannedTask):
    confidence: float = 0.8
    source_snippet: Optional[str] = None


class TaskPlanningResult(BaseModel):
    project_theme: str
    tasks: List[PlannedTask]


class ImageTaskExtractionResult(BaseModel):
    scene_summary: str
    detected_context: str
    tasks: List[ImageTaskCandidate]
    warnings: List[str] = Field(default_factory=list)


class PlannedScheduleItem(BaseModel):
    task_id: str
    start_time: str
    end_time: str
    reason: str


class DayScheduleGenerationResult(BaseModel):
    schedule: List[PlannedScheduleItem]
    suggestions: List[str] = Field(default_factory=list)
    efficiency_score: int = 8


class AgentToolCallTrace(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "completed", "failed"] = "pending"
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentTraceEvent(BaseModel):
    timestamp: datetime
    event_type: str
    stage: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserPreferences(BaseModel):
    user_id: str = "default"
    display_name: Optional[str] = None
    work_start_time: str = "09:00"
    work_end_time: str = "18:00"
    peak_focus_period: Literal["morning", "afternoon", "evening", "split"] = "morning"
    planning_style: Literal["structured", "balanced", "flexible"] = "balanced"
    priority_preference: Literal["deadline_first", "impact_first", "balanced"] = "balanced"
    max_daily_focus_hours: float = 6.0
    preferred_task_duration_hours: float = 2.0
    break_interval_minutes: int = 90
    avoid_time_ranges: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class UserPreferencesUpdate(BaseModel):
    display_name: Optional[str] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    peak_focus_period: Optional[Literal["morning", "afternoon", "evening", "split"]] = None
    planning_style: Optional[Literal["structured", "balanced", "flexible"]] = None
    priority_preference: Optional[Literal["deadline_first", "impact_first", "balanced"]] = None
    max_daily_focus_hours: Optional[float] = None
    preferred_task_duration_hours: Optional[float] = None
    break_interval_minutes: Optional[int] = None
    avoid_time_ranges: Optional[List[str]] = None


class UserMemoryItem(BaseModel):
    id: Optional[str] = None
    user_id: str = "default"
    category: Literal["preference", "constraint", "goal", "habit", "context"] = "context"
    source: Literal["user", "system", "inferred"] = "user"
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class UserMemoryCreate(BaseModel):
    category: Literal["preference", "constraint", "goal", "habit", "context"] = "context"
    source: Literal["user", "system", "inferred"] = "user"
    content: str
    tags: List[str] = Field(default_factory=list)


class UserPlanningContext(BaseModel):
    preferences: UserPreferences
    relevant_memories: List[UserMemoryItem] = Field(default_factory=list)
    behavior_summary: str = ""
    prompt_context: str = ""


class TaskPlanningTrace(BaseModel):
    execution_status: AgentExecutionStatus = AgentExecutionStatus.PENDING
    current_step: str = "queued"
    input_modality: Literal["text", "image"] = "text"
    task_type: Optional[str] = None
    project_theme: Optional[str] = None
    source_summary: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    events: List[AgentTraceEvent] = Field(default_factory=list)
    preference_snapshot: Optional[UserPreferences] = None
    relevant_memories: List[UserMemoryItem] = Field(default_factory=list)
    behavior_summary: str = ""
    extracted_candidates: List[ImageTaskCandidate] = Field(default_factory=list)
    planned_tasks: List[PlannedTask] = Field(default_factory=list)
    tool_calls: List[AgentToolCallTrace] = Field(default_factory=list)
    created_tasks: List[Task] = Field(default_factory=list)


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
    trace: Optional[TaskPlanningTrace] = None


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
