import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.db.database import db
from app.core.logging_utils import log_eval_event
from app.models.schemas import UserMemoryCreate, UserPreferencesUpdate
from app.services.memory_service import MemoryService


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_PATH = EVALS_DIR / "results" / "latest.json"
TEXT_DATASET_PATH = EVALS_DIR / "text_planning_dataset.json"
IMAGE_DATASET_PATH = EVALS_DIR / "image_task_dataset.json"
MEMORY_DATASET_PATH = EVALS_DIR / "memory_hit_dataset.json"


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 3)


def _evaluate_text_planning_offline() -> dict[str, Any]:
    dataset = _load_dataset(TEXT_DATASET_PATH)
    schema_success = 0

    for item in dataset:
        if item.get("id") and item.get("goal") and item.get("expected_theme"):
            schema_success += 1

    return {
        "dataset_size": len(dataset),
        "schema_success_count": schema_success,
        "schema_success_rate": _safe_rate(schema_success, len(dataset)),
        "mode": "offline_smoke",
        "notes": "Offline mode validates dataset readiness and runner coverage. Use live mode later for model-quality metrics.",
    }


def _evaluate_image_task_offline() -> dict[str, Any]:
    dataset = _load_dataset(IMAGE_DATASET_PATH)
    schema_success = 0

    for item in dataset:
        if (
            item.get("id")
            and item.get("image_hint")
            and isinstance(item.get("expected_tasks"), int)
            and item["expected_tasks"] >= 0
        ):
            schema_success += 1

    return {
        "dataset_size": len(dataset),
        "schema_success_count": schema_success,
        "schema_success_rate": _safe_rate(schema_success, len(dataset)),
        "mode": "offline_smoke",
        "notes": "Offline mode validates multimodal eval inputs and expected task-count labels.",
    }


def _seed_memory_eval_state() -> None:
    MemoryService.update_preferences(
        payload=UserPreferencesUpdate(planning_style="balanced")
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="constraint",
            content="Avoid meetings before 10am when planning work.",
            tags=["morning", "constraint"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="goal",
            content="Prioritize AI agent career work and portfolio tasks.",
            tags=["career", "ai", "goal"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="preference",
            content="I prefer one-hour focus blocks for deep work.",
            tags=["duration", "focus", "preference"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="preference",
            content="Schedule high-impact tasks first when possible.",
            tags=["priority", "impact", "preference"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="habit",
            content="Keep afternoon time for implementation work.",
            tags=["afternoon", "implementation", "habit"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="preference",
            content="Use flexible planning on weekends.",
            tags=["weekend", "flexible", "preference"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="constraint",
            content="Do not overload one day with too much deep work.",
            tags=["deep-work", "constraint"],
        )
    )
    MemoryService.create_memory(
        payload=_memory_payload(
            category="context",
            content="Current release work is active and should stay visible in planning.",
            tags=["release", "context"],
        )
    )


def _memory_payload(*, category: str, content: str, tags: list[str]):
    return UserMemoryCreate(category=category, content=content, tags=tags)


def _evaluate_memory_hit() -> dict[str, Any]:
    dataset = _load_dataset(MEMORY_DATASET_PATH)
    db.clear_all()
    _seed_memory_eval_state()

    matched_count = 0
    case_results = []
    for item in dataset:
        planning_context = MemoryService.build_planning_context(prompt=item["prompt"])
        matched_categories = [
            memory.category for memory in planning_context.relevant_memories if memory.relevance_score
        ]
        matched = item["expected_category"] in matched_categories
        if matched:
            matched_count += 1
        case_results.append(
            {
                "id": item["id"],
                "prompt": item["prompt"],
                "expected_category": item["expected_category"],
                "matched_categories": matched_categories,
                "matched": matched,
            }
        )

    return {
        "dataset_size": len(dataset),
        "matched_count": matched_count,
        "memory_hit_rate": _safe_rate(matched_count, len(dataset)),
        "cases": case_results,
        "mode": "offline_local",
    }


def run_all_evals(mode: str = "offline", output_path: Path | None = None) -> dict[str, Any]:
    if mode != "offline":
        raise ValueError("Only offline mode is implemented in this runner for now.")

    log_eval_event("eval_run_started", mode=mode)
    result = {
        "generated_at": datetime.now().isoformat(),
        "mode": mode,
        "summary": {
            "text_planning": _evaluate_text_planning_offline(),
            "image_task": _evaluate_image_task_offline(),
            "memory_hit": _evaluate_memory_hit(),
        },
    }

    target_path = output_path or DEFAULT_RESULTS_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log_eval_event(
        "eval_run_completed",
        mode=mode,
        output_path=str(target_path),
        text_schema_success_rate=result["summary"]["text_planning"]["schema_success_rate"],
        image_schema_success_rate=result["summary"]["image_task"]["schema_success_rate"],
        memory_hit_rate=result["summary"]["memory_hit"]["memory_hit_rate"],
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TaskGenie local evals.")
    parser.add_argument("--mode", default="offline", choices=["offline"])
    parser.add_argument("--output", default=str(DEFAULT_RESULTS_PATH))
    args = parser.parse_args()

    result = run_all_evals(mode=args.mode, output_path=Path(args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
