from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from app.models.schemas import PlannedTask, Task, TaskCreate, TaskPlanningResult
from app.services.llm_service import LLMService
from app.services.tool_registry import task_tool_registry


@dataclass
class PlannedToolCall:
    tool_name: str
    arguments: Dict[str, Any]

    def to_trace_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key, value in self.arguments.items():
            if hasattr(value, "model_dump"):
                payload[key] = value.model_dump(mode="json")
            else:
                payload[key] = value
        return payload


@dataclass
class WorkflowRunResult:
    task_type: str
    project_theme: str
    planned_tasks: List[PlannedTask]
    created_tasks: List[Task]
    tool_calls: List[PlannedToolCall]


class TaskPlanningWorkflow:
    @staticmethod
    def run(prompt: str, max_tasks: int, task_type: str, now: datetime) -> WorkflowRunResult:
        planning_result = TaskPlanningWorkflow.plan_tasks(
            prompt=prompt,
            max_tasks=max_tasks,
            task_type=task_type,
            now=now,
        )
        tool_calls = TaskPlanningWorkflow.build_execution_plan(
            planned_tasks=planning_result.tasks,
            project_theme=planning_result.project_theme,
            max_tasks=max_tasks,
            now=now,
        )
        created_tasks = TaskPlanningWorkflow.execute_plan(tool_calls)

        return WorkflowRunResult(
            task_type=task_type,
            project_theme=planning_result.project_theme,
            planned_tasks=planning_result.tasks,
            created_tasks=created_tasks,
            tool_calls=tool_calls,
        )

    @staticmethod
    def plan_tasks(prompt: str, max_tasks: int, task_type: str, now: datetime) -> TaskPlanningResult:
        planning_result = LLMService.generate_structured_output(
            system_prompt=TaskPlanningWorkflow._build_planner_prompt(
                task_type=task_type,
                max_tasks=max_tasks,
                now=now,
            ),
            user_prompt=f"User goal:\n{prompt}",
            response_model=TaskPlanningResult,
            temperature=0.7,
            max_tokens=1400,
        )

        if not planning_result.tasks:
            raise ValueError("AI did not return any tasks")

        return planning_result

    @staticmethod
    def _build_planner_prompt(task_type: str, max_tasks: int, now: datetime) -> str:
        return f"""
You are an AI planning assistant for a task management product.
Current time: {now.isoformat(timespec="minutes")}
Task type: {task_type}

First think like a planner. Break the user's goal into actionable tasks.
Return exactly one JSON object that matches this schema:
{{
  "project_theme": "short project theme",
  "tasks": [
    {{
      "name": "concrete action",
      "description": "clear execution details",
      "priority": "low|medium|high",
      "estimated_hours": 2.0,
      "due_date": "optional ISO datetime or null"
    }}
  ]
}}

Requirements:
- Return between 1 and {max_tasks} tasks.
- Make each task actionable and specific.
- Prefer realistic time estimates between 0.5 and 6 hours.
- Use concise project theme text.
- Do not include markdown fences.
""".strip()

    @staticmethod
    def build_execution_plan(
        *,
        planned_tasks: List[PlannedTask],
        project_theme: str,
        max_tasks: int,
        now: datetime,
    ) -> List[PlannedToolCall]:
        tool_calls: List[PlannedToolCall] = []

        for index, planned_task in enumerate(planned_tasks[:max_tasks], start=1):
            tool_calls.append(
                PlannedToolCall(
                    tool_name="create_task",
                    arguments={
                        "task_data": TaskCreate(
                            name=TaskPlanningWorkflow._normalize_task_name(
                                project_theme=project_theme,
                                step_index=index,
                                task_name=planned_task.name,
                            ),
                            description=TaskPlanningWorkflow._normalize_description(
                                planned_task.description
                            ),
                            priority=planned_task.priority,
                            estimated_hours=max(
                                0.5,
                                min(6.0, float(planned_task.estimated_hours or 2.0)),
                            ),
                            due_date=planned_task.due_date
                            or TaskPlanningWorkflow._infer_due_date(
                                base_time=now,
                                priority=planned_task.priority,
                                index=index,
                            ),
                        )
                    },
                )
            )

        return tool_calls

    @staticmethod
    def execute_plan(
        tool_calls: List[PlannedToolCall],
        on_step: Optional[
            Callable[[int, PlannedToolCall, Optional[Task], Optional[Exception]], None]
        ] = None,
    ) -> List[Task]:
        created_tasks: List[Task] = []
        for index, tool_call in enumerate(tool_calls):
            try:
                result = task_tool_registry.execute(
                    tool_call.tool_name,
                    **tool_call.arguments,
                )
            except Exception as exc:
                if on_step:
                    on_step(index, tool_call, None, exc)
                raise

            created_tasks.append(result)
            if on_step:
                on_step(index, tool_call, result, None)

        return created_tasks

    @staticmethod
    def _normalize_task_name(project_theme: str, step_index: int, task_name: str) -> str:
        name = task_name.strip() or f"Complete step {step_index}"
        return f"{project_theme} Step{step_index}: {name}"

    @staticmethod
    def _normalize_description(description: str) -> str:
        description = (description or "").strip()
        if len(description) >= 20:
            return description
        if description:
            return f"{description}. Add concrete execution steps, acceptance criteria, and expected output."
        return "Add concrete execution steps, acceptance criteria, and expected output."

    @staticmethod
    def _infer_due_date(base_time: datetime, priority: str, index: int) -> datetime:
        if priority == "high" or index == 1:
            days_offset = 1 + (index - 1) * 0.5
        elif priority == "medium":
            days_offset = 2 + (index - 1) * 1.5
        else:
            days_offset = 4 + (index - 1) * 2

        due_date = base_time + timedelta(days=days_offset)
        return due_date.replace(hour=18, minute=0, second=0, microsecond=0)
