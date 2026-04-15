from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from app.services.task_service import TaskService


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, handler: Callable[..., Any]) -> None:
        self._tools[name] = ToolDefinition(name=name, description=description, handler=handler)

    def execute(self, name: str, **kwargs):
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler(**kwargs)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())


task_tool_registry = ToolRegistry()
task_tool_registry.register(
    "create_task",
    "Create a task in persistent storage.",
    lambda task_data: TaskService.create_task(task_data),
)
task_tool_registry.register(
    "update_task",
    "Update an existing task.",
    lambda task_id, task_update: TaskService.update_task(task_id, task_update),
)
task_tool_registry.register(
    "delete_task",
    "Delete an existing task.",
    lambda task_id: TaskService.delete_task(task_id),
)
task_tool_registry.register(
    "list_tasks",
    "List all tasks.",
    lambda: TaskService.get_all_tasks(),
)
task_tool_registry.register(
    "get_stats",
    "Get aggregate task statistics.",
    lambda: TaskService.get_task_stats(),
)
