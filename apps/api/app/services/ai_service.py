import hashlib
import uuid
from datetime import datetime
from typing import List, Optional

from app.db.database import db
from app.models.schemas import (
    AIJobStatus,
    AgentExecutionStatus,
    AgentTraceEvent,
    AgentToolCallTrace,
    DaySchedule,
    DayScheduleGenerationResult,
    Task,
    TaskPlanningTrace,
    TaskScheduleItem,
)
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.task_planning_workflow import TaskPlanningWorkflow


class AIService:
    @staticmethod
    async def process_task_planning(job_id: str, prompt: str, max_tasks: int):
        trace: Optional[TaskPlanningTrace] = None
        try:
            now = datetime.now()
            task_type = AIService._analyze_task_type(prompt)
            trace = TaskPlanningTrace(
                execution_status=AgentExecutionStatus.PLANNING,
                current_step="planning",
                task_type=task_type,
                started_at=now,
            )
            planning_context = MemoryService.build_planning_context(prompt=prompt)
            trace.preference_snapshot = planning_context.preferences
            trace.relevant_memories = planning_context.relevant_memories
            trace.behavior_summary = planning_context.behavior_summary
            AIService._append_trace_event(
                trace,
                event_type="memory_loaded",
                stage="context",
                message="Loaded user preferences and relevant memories.",
                metadata={
                    "memory_count": len(planning_context.relevant_memories),
                    "planning_style": planning_context.preferences.planning_style,
                },
            )
            AIService._append_trace_event(
                trace,
                event_type="planning_started",
                stage="planning",
                message="Started analyzing the user goal and generating a task plan.",
                metadata={
                    "task_type": task_type,
                    "max_tasks": max_tasks,
                },
            )
            AIService._update_job_state(
                job_id,
                status=AIJobStatus.PROCESSING,
                trace=trace,
                error=None,
            )

            planning_result = TaskPlanningWorkflow.plan_tasks(
                prompt=prompt,
                max_tasks=max_tasks,
                task_type=task_type,
                now=now,
                planning_context=planning_context.prompt_context,
            )
            trace.project_theme = planning_result.project_theme
            trace.planned_tasks = planning_result.tasks
            AIService._append_trace_event(
                trace,
                event_type="planning_completed",
                stage="planning",
                message="Generated a structured task plan.",
                metadata={
                    "project_theme": planning_result.project_theme,
                    "planned_task_count": len(planning_result.tasks),
                },
            )

            tool_calls = TaskPlanningWorkflow.build_execution_plan(
                planned_tasks=planning_result.tasks,
                project_theme=planning_result.project_theme,
                max_tasks=max_tasks,
                now=now,
            )
            trace.execution_status = AgentExecutionStatus.EXECUTING
            trace.current_step = "executing"
            trace.tool_calls = [
                AgentToolCallTrace(
                    tool_name=tool_call.tool_name,
                    arguments=tool_call.to_trace_payload(),
                )
                for tool_call in tool_calls
            ]
            AIService._append_trace_event(
                trace,
                event_type="execution_started",
                stage="execution",
                message="Converted the plan into internal tool calls.",
                metadata={
                    "tool_call_count": len(tool_calls),
                },
            )
            AIService._update_job_state(
                job_id,
                status=AIJobStatus.PROCESSING,
                trace=trace,
            )

            created_tasks = TaskPlanningWorkflow.execute_plan(
                tool_calls,
                on_step=lambda index, _tool_call, result, error: AIService._record_tool_step(
                    job_id=job_id,
                    trace=trace,
                    index=index,
                    result=result,
                    error=error,
                ),
            )
            trace.created_tasks = created_tasks
            trace.execution_status = AgentExecutionStatus.COMPLETED
            trace.current_step = "completed"
            trace.finished_at = datetime.now()
            AIService._append_trace_event(
                trace,
                event_type="run_completed",
                stage="completion",
                message="Completed the AI planning workflow successfully.",
                metadata={
                    "created_task_count": len(created_tasks),
                },
            )

            AIService._update_job_state(
                job_id,
                status=AIJobStatus.COMPLETED,
                result=[task.model_dump(mode="json") for task in created_tasks],
                trace=trace,
                error=None,
            )
        except Exception as exc:
            failed_trace = trace or TaskPlanningTrace(
                execution_status=AgentExecutionStatus.FAILED,
                current_step="failed",
                started_at=datetime.now(),
            )
            failed_trace.execution_status = AgentExecutionStatus.FAILED
            failed_trace.current_step = "failed"
            failed_trace.finished_at = datetime.now()
            AIService._append_trace_event(
                failed_trace,
                event_type="run_failed",
                stage="failure",
                message="The AI planning workflow failed.",
                metadata={"error": str(exc)},
            )
            AIService._update_job_state(
                job_id,
                status=AIJobStatus.FAILED,
                trace=failed_trace,
                error=f"AI task planning failed: {exc}",
            )

    @staticmethod
    async def process_day_schedule(
        job_id: str,
        date_str: str,
        task_ids: Optional[List[str]] = None,
        force_regenerate: bool = False,
    ):
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if task_ids:
                tasks_to_schedule = []
                for task_id in task_ids:
                    task = db.get_task(task_id)
                    if task and not task.completed:
                        tasks_to_schedule.append(task)
            else:
                tasks_to_schedule = db.get_tasks_for_date(target_date)

            if not tasks_to_schedule:
                empty_schedule = DaySchedule(
                    id=str(uuid.uuid4()),
                    date=target_date,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    schedule_items=[],
                    suggestions=["No tasks are scheduled for this day yet."],
                    total_hours=0,
                    efficiency_score=10,
                    task_version="",
                )
                db.create_day_schedule(date_str, empty_schedule)

                job = db.get_ai_job(job_id)
                job.status = AIJobStatus.COMPLETED
                job.result = {
                    "date": date_str,
                    "has_schedule": True,
                    "schedule": empty_schedule.model_dump(mode="json"),
                    "tasks_changed": False,
                }
                db.update_ai_job(job_id, job)
                return

            current_task_version = AIService._generate_task_version(tasks_to_schedule)
            if not force_regenerate:
                existing_schedule = db.get_day_schedule(date_str)
                if existing_schedule and existing_schedule.task_version == current_task_version:
                    job = db.get_ai_job(job_id)
                    job.status = AIJobStatus.COMPLETED
                    job.result = {
                        "date": date_str,
                        "has_schedule": True,
                        "schedule": existing_schedule.model_dump(mode="json"),
                        "tasks_changed": False,
                    }
                    db.update_ai_job(job_id, job)
                    return

            schedule_result = AIService._generate_day_schedule(tasks_to_schedule, target_date)

            day_schedule = DaySchedule(
                id=str(uuid.uuid4()),
                date=target_date,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                schedule_items=schedule_result["schedule_items"],
                suggestions=schedule_result["suggestions"],
                total_hours=schedule_result["total_hours"],
                efficiency_score=schedule_result["efficiency_score"],
                task_version=current_task_version,
            )

            db.create_day_schedule(date_str, day_schedule)

            job = db.get_ai_job(job_id)
            job.status = AIJobStatus.COMPLETED
            job.result = {
                "date": date_str,
                "has_schedule": True,
                "schedule": day_schedule.model_dump(mode="json"),
                "tasks_changed": False,
            }
            db.update_ai_job(job_id, job)
        except Exception as exc:
            job = db.get_ai_job(job_id)
            job.status = AIJobStatus.FAILED
            job.error = str(exc)
            db.update_ai_job(job_id, job)

    @staticmethod
    def _build_day_schedule_system_prompt(target_date: str, task_ids: List[str]) -> str:
        return f"""
You are an AI scheduling assistant.
Schedule tasks for {target_date}.
Return exactly one JSON object with this schema:
{{
  "schedule": [
    {{
      "task_id": "task id",
      "start_time": "09:00",
      "end_time": "10:30",
      "reason": "why it is scheduled here"
    }}
  ],
  "suggestions": ["short suggestion"],
  "efficiency_score": 8
}}

Guidelines:
- Prioritize overdue and high-priority tasks.
- Avoid impossible overlaps.
- Use work hours between 09:00 and 22:00.
- Keep reasons short and concrete.
- Only use task ids from this list: {task_ids}
- Do not include markdown fences.
""".strip()

    @staticmethod
    def _analyze_task_type(prompt: str) -> str:
        prompt_analysis = prompt.lower()
        if any(
            keyword in prompt_analysis
            for keyword in ["study", "learn", "research", "学习", "掌握", "研究"]
        ):
            return "learning"
        if any(
            keyword in prompt_analysis
            for keyword in ["build", "develop", "design", "implement", "开发", "设计", "实现", "制作"]
        ):
            return "development"
        if any(
            keyword in prompt_analysis
            for keyword in ["plan", "organize", "arrange", "计划", "整理", "安排"]
        ):
            return "planning"
        if any(
            keyword in prompt_analysis
            for keyword in ["write", "draft", "submit", "写", "撰写", "提交"]
        ):
            return "writing"
        return "general"

    @staticmethod
    def _generate_task_version(tasks: List[Task]) -> str:
        task_info = []
        for task in sorted(tasks, key=lambda current_task: current_task.id):
            task_info.append(
                f"{task.id}:{task.name}:{task.completed}:{task.priority}:{task.due_date}:{task.estimated_hours}"
            )
        return hashlib.md5("|".join(task_info).encode()).hexdigest()

    @staticmethod
    def _generate_day_schedule(tasks: List[Task], target_date) -> dict:
        tasks_payload = [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description or "",
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "estimated_hours": task.estimated_hours or 2.0,
                "is_overdue": bool(task.due_date and task.due_date < datetime.now()),
            }
            for task in tasks
        ]

        llm_result = LLMService.generate_structured_output(
            system_prompt=AIService._build_day_schedule_system_prompt(
                str(target_date),
                [task["id"] for task in tasks_payload],
            ),
            user_prompt=f"Tasks to schedule:\n{tasks_payload}",
            response_model=DayScheduleGenerationResult,
            temperature=0.6,
            max_tokens=900,
        )

        schedule_items = []
        total_hours = 0.0

        for item in llm_result.schedule:
            task = db.get_task(item.task_id)
            if not task:
                continue

            start_hour, start_min = map(int, item.start_time.split(":"))
            end_hour, end_min = map(int, item.end_time.split(":"))
            duration = (end_hour * 60 + end_min - start_hour * 60 - start_min) / 60
            total_hours += duration

            schedule_items.append(
                TaskScheduleItem(
                    task_id=item.task_id,
                    task_name=task.name,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    duration=duration,
                    priority=task.priority,
                    reason=item.reason or "Scheduled based on priority and available time.",
                )
            )

        return {
            "schedule_items": schedule_items,
            "suggestions": llm_result.suggestions,
            "total_hours": total_hours,
            "efficiency_score": llm_result.efficiency_score,
        }

    @staticmethod
    def _record_tool_step(
        *,
        job_id: str,
        trace: TaskPlanningTrace,
        index: int,
        result: Optional[Task],
        error: Optional[Exception],
    ) -> None:
        tool_call = trace.tool_calls[index]
        if error is not None:
            tool_call.status = "failed"
            tool_call.error = str(error)
            trace.execution_status = AgentExecutionStatus.FAILED
            trace.current_step = "failed"
            AIService._append_trace_event(
                trace,
                event_type="tool_failed",
                stage="execution",
                message=f"Tool call {index + 1} failed.",
                metadata={
                    "tool_name": tool_call.tool_name,
                    "tool_index": index,
                    "error": str(error),
                },
            )
        else:
            tool_call.status = "completed"
            tool_call.output = (
                {
                    "task_id": result.id,
                    "task_name": result.name,
                }
                if result is not None
                else None
            )
            if result is not None:
                trace.created_tasks = [
                    current_task
                    for current_task in trace.created_tasks
                    if current_task.id != result.id
                ]
                trace.created_tasks.append(result)
            AIService._append_trace_event(
                trace,
                event_type="tool_completed",
                stage="execution",
                message=f"Tool call {index + 1} completed.",
                metadata={
                    "tool_name": tool_call.tool_name,
                    "tool_index": index,
                    "task_id": result.id if result is not None else None,
                },
            )

        AIService._update_job_state(
            job_id,
            status=AIJobStatus.PROCESSING if error is None else AIJobStatus.FAILED,
            trace=trace,
        )

    @staticmethod
    def _update_job_state(
        job_id: str,
        *,
        status: AIJobStatus,
        trace: Optional[TaskPlanningTrace] = None,
        result=None,
        error: Optional[str] = None,
    ) -> None:
        job = db.get_ai_job(job_id)
        if not job:
            return

        job.status = status
        if trace is not None:
            job.trace = trace
        if result is not None:
            job.result = result
        if error is not None or status != AIJobStatus.FAILED:
            job.error = error

        db.update_ai_job(job_id, job)

    @staticmethod
    def _append_trace_event(
        trace: TaskPlanningTrace,
        *,
        event_type: str,
        stage: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> None:
        trace.events.append(
            AgentTraceEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                stage=stage,
                message=message,
                metadata=metadata or {},
            )
        )
