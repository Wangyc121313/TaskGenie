import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, List, Optional

from app.models.schemas import AgentToolCallTrace, PlannedTask, Task
from app.services.tool_registry import task_tool_registry


def build_task_creation_tool_calls(
    *,
    planned_tasks: List[PlannedTask],
    project_theme: str,
    max_tasks: int,
    now: datetime,
) -> List[AgentToolCallTrace]:
    tool_calls: List[AgentToolCallTrace] = []

    for index, planned_task in enumerate(planned_tasks[:max_tasks], start=1):
        definition = task_tool_registry.get_definition("create_task")
        tool_calls.append(
            AgentToolCallTrace(
                call_id=str(uuid.uuid4()),
                tool_name=definition.name,
                arguments={
                    "task_data": {
                        "name": _normalize_task_name(
                            project_theme=project_theme,
                            step_index=index,
                            task_name=planned_task.name,
                        ),
                        "description": _normalize_description(planned_task.description),
                        "priority": planned_task.priority,
                        "estimated_hours": max(
                            0.5,
                            min(6.0, float(planned_task.estimated_hours or 2.0)),
                        ),
                        "due_date": (
                            planned_task.due_date.isoformat()
                            if planned_task.due_date is not None
                            else _infer_due_date(
                                base_time=now,
                                priority=planned_task.priority,
                                index=index,
                            ).isoformat()
                        ),
                    }
                },
                input_schema=definition.input_schema,
                output_schema=definition.output_schema,
                side_effect_level=definition.side_effect_level,
                requires_confirmation=definition.requires_confirmation,
                retryable=definition.retryable,
            )
        )

    return tool_calls


def execute_tool_calls(
    tool_calls: List[AgentToolCallTrace],
    *,
    on_step: Optional[
        Callable[[int, AgentToolCallTrace, Optional[Any], Optional[Exception]], None]
    ] = None,
) -> List[Any]:
    results: List[Any] = []
    for index, tool_call in enumerate(tool_calls):
        started_at = time.perf_counter()
        try:
            result = task_tool_registry.execute(tool_call.tool_name, **tool_call.arguments)
        except Exception as exc:
            tool_call.status = "failed"
            tool_call.error = str(exc)
            tool_call.latency_ms = int((time.perf_counter() - started_at) * 1000)
            tool_call.executed_at = datetime.now()
            if on_step:
                on_step(index, tool_call, None, exc)
            raise

        tool_call.status = "completed"
        tool_call.executed_at = datetime.now()
        tool_call.latency_ms = int((time.perf_counter() - started_at) * 1000)
        tool_call.output = _serialize_result(result)
        results.append(result)
        if on_step:
            on_step(index, tool_call, result, None)

    return results


def _serialize_result(result: Any) -> Optional[dict]:
    if result is None:
        return None
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    if isinstance(result, dict):
        return result
    if isinstance(result, bool):
        return {"success": result}
    return {"value": str(result)}


def _normalize_task_name(project_theme: str, step_index: int, task_name: str) -> str:
    name = task_name.strip() or f"Complete step {step_index}"
    return f"{project_theme} Step {step_index}: {name}"


def _normalize_description(description: str) -> str:
    description = (description or "").strip()
    if len(description) >= 20:
        return description
    if description:
        return f"{description}. Add concrete execution steps, acceptance criteria, and expected output."
    return "Add concrete execution steps, acceptance criteria, and expected output."


def _infer_due_date(base_time: datetime, priority: str, index: int) -> datetime:
    if priority == "high" or index == 1:
        days_offset = 1 + (index - 1) * 0.5
    elif priority == "medium":
        days_offset = 2 + (index - 1) * 1.5
    else:
        days_offset = 4 + (index - 1) * 2

    due_date = base_time + timedelta(days=days_offset)
    return due_date.replace(hour=18, minute=0, second=0, microsecond=0)
