from typing import Iterable

from app.models.schemas import AgentToolCallTrace


def should_require_confirmation(
    tool_calls: Iterable[AgentToolCallTrace],
    *,
    auto_execute: bool,
) -> bool:
    if auto_execute:
        return False
    return any(tool_call.requires_confirmation for tool_call in tool_calls)
