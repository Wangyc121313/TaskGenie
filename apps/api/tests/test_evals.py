import json
from pathlib import Path
import shutil
import uuid

from evals.run_evals import run_all_evals


def _make_workspace_tmp_dir() -> Path:
    tmp_dir = Path("tests") / ".tmp" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def test_run_all_evals_offline_writes_summary():
    tmp_dir = _make_workspace_tmp_dir()
    output_path = tmp_dir / "latest.json"

    try:
        result = run_all_evals(mode="offline", output_path=output_path)

        assert result["mode"] == "offline"
        assert "generated_at" in result
        assert "summary" in result
        assert "text_planning" in result["summary"]
        assert "image_task" in result["summary"]
        assert "memory_hit" in result["summary"]
        assert result["summary"]["memory_hit"]["dataset_size"] == 10
        assert output_path.exists()

        persisted = json.loads(output_path.read_text(encoding="utf-8"))
        assert persisted["summary"]["memory_hit"]["dataset_size"] == 10
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_run_all_evals_offline_reports_core_metrics():
    tmp_dir = _make_workspace_tmp_dir()
    try:
        result = run_all_evals(mode="offline", output_path=tmp_dir / "metrics.json")

        text_summary = result["summary"]["text_planning"]
        image_summary = result["summary"]["image_task"]
        memory_summary = result["summary"]["memory_hit"]

        assert "schema_success_rate" in text_summary
        assert "dataset_size" in text_summary
        assert "schema_success_rate" in image_summary
        assert "memory_hit_rate" in memory_summary
        assert memory_summary["matched_count"] <= memory_summary["dataset_size"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
