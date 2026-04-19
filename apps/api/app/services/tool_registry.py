from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.models.schemas import MCPToolDescriptor, MCPToolCallResponse, ToolDefinitionSchema, ToolSideEffectLevel
from app.models.schemas import TaskCreate, TaskUpdate, UserPreferencesUpdate
from app.services.task_service import TaskService
from app.services.memory_service import MemoryService


def _model_schema(model_cls: Optional[type[BaseModel]]) -> Dict[str, Any]:
    if model_cls is None:
        return {}
    return model_cls.model_json_schema()


def _parse_kwargs_with_models(
    kwargs: Dict[str, Any],
    models: Dict[str, type[BaseModel]],
) -> Dict[str, Any]:
    parsed = dict(kwargs)
    for field_name, model_cls in models.items():
        if field_name in parsed and isinstance(parsed[field_name], dict):
            parsed[field_name] = model_cls.model_validate(parsed[field_name])
    return parsed


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    side_effect_level: ToolSideEffectLevel = ToolSideEffectLevel.READ
    requires_confirmation: bool = False
    retryable: bool = False
    argument_models: Dict[str, type[BaseModel]] = field(default_factory=dict)

    def parse_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        return _parse_kwargs_with_models(kwargs, self.argument_models)

    def to_schema(self) -> ToolDefinitionSchema:
        return ToolDefinitionSchema(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            side_effect_level=self.side_effect_level,
            requires_confirmation=self.requires_confirmation,
            retryable=self.retryable,
        )


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        *,
        name: str,
        description: str,
        handler: Callable[..., Any],
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        side_effect_level: ToolSideEffectLevel = ToolSideEffectLevel.READ,
        requires_confirmation: bool = False,
        retryable: bool = False,
        argument_models: Optional[Dict[str, type[BaseModel]]] = None,
    ) -> None:
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            side_effect_level=side_effect_level,
            requires_confirmation=requires_confirmation,
            retryable=retryable,
            argument_models=argument_models or {},
        )

    def get_definition(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def execute(self, name: str, **kwargs):
        definition = self.get_definition(name)
        parsed_kwargs = definition.parse_kwargs(kwargs)
        return definition.handler(**parsed_kwargs)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def list_mcp_tools(self) -> List[MCPToolDescriptor]:
        return [
            MCPToolDescriptor(
                name=definition.name,
                description=definition.description,
                inputSchema=definition.input_schema,
                annotations={
                    "sideEffectLevel": definition.side_effect_level.value,
                    "requiresConfirmation": definition.requires_confirmation,
                    "retryable": definition.retryable,
                },
            )
            for definition in self.list_tools()
        ]

    def call_mcp_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> MCPToolCallResponse:
        result = self.execute(name, **(arguments or {}))
        encoded_result = jsonable_encoder(result)
        return MCPToolCallResponse(
            content=[
                {
                    "type": "text",
                    "text": f"Tool {name} executed successfully.",
                }
            ],
            structuredContent={
                "tool": name,
                "result": encoded_result,
            },
            isError=False,
        )


task_tool_registry = ToolRegistry()
task_tool_registry.register(
    name="create_task",
    description="Create a task in persistent storage.",
    handler=lambda task_data: TaskService.create_task(task_data),
    input_schema={"task_data": _model_schema(TaskCreate)},
    output_schema=_model_schema(TaskCreate),
    side_effect_level=ToolSideEffectLevel.WRITE,
    requires_confirmation=True,
    retryable=True,
    argument_models={"task_data": TaskCreate},
)
task_tool_registry.register(
    name="update_task",
    description="Update an existing task.",
    handler=lambda task_id, task_update: TaskService.update_task(task_id, task_update),
    input_schema={"task_id": {"type": "string"}, "task_update": _model_schema(TaskUpdate)},
    output_schema={"type": "object"},
    side_effect_level=ToolSideEffectLevel.WRITE,
    requires_confirmation=True,
    retryable=True,
    argument_models={"task_update": TaskUpdate},
)
task_tool_registry.register(
    name="delete_task",
    description="Delete an existing task.",
    handler=lambda task_id: TaskService.delete_task(task_id),
    input_schema={"task_id": {"type": "string"}},
    output_schema={"type": "boolean"},
    side_effect_level=ToolSideEffectLevel.DESTRUCTIVE,
    requires_confirmation=True,
    retryable=False,
)
task_tool_registry.register(
    name="list_tasks",
    description="List all tasks.",
    handler=lambda: TaskService.get_all_tasks(),
    output_schema={"type": "array"},
)
task_tool_registry.register(
    name="get_stats",
    description="Get aggregate task statistics.",
    handler=lambda: TaskService.get_task_stats(),
    output_schema={"type": "object"},
)
task_tool_registry.register(
    name="search_recent_tasks",
    description="Search recent tasks by keyword in title or description.",
    handler=lambda query, limit=5: [
        task
        for task in TaskService.get_all_tasks()
        if query.lower() in task.name.lower() or query.lower() in (task.description or "").lower()
    ][:limit],
    input_schema={
        "query": {"type": "string"},
        "limit": {"type": "integer", "default": 5},
    },
    output_schema={"type": "array"},
)
task_tool_registry.register(
    name="save_preference",
    description="Update structured user preferences.",
    handler=lambda preference_update: MemoryService.update_preferences(preference_update),
    input_schema={"preference_update": _model_schema(UserPreferencesUpdate)},
    output_schema={"type": "object"},
    side_effect_level=ToolSideEffectLevel.WRITE,
    requires_confirmation=True,
    retryable=True,
    argument_models={"preference_update": UserPreferencesUpdate},
)
task_tool_registry.register(
    name="schedule_day",
    description="Persist a generated day schedule for a specific date.",
    handler=lambda date_str, schedule: {"date": date_str, "saved_at": datetime.now().isoformat()},
    input_schema={
        "date_str": {"type": "string"},
        "schedule": {"type": "object"},
    },
    output_schema={"type": "object"},
    side_effect_level=ToolSideEffectLevel.WRITE,
    requires_confirmation=False,
    retryable=True,
)
