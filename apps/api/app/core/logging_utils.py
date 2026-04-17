import json
import logging
from typing import Any, Dict


logger = logging.getLogger("taskgenie.agent")


def log_agent_event(event_type: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {"event_type": event_type, **fields}
    logger.info(json.dumps(payload, default=str, ensure_ascii=False))
