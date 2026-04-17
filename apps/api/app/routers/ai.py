import base64
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agent.runtime import AgentRuntime
from app.core.config import current_settings
from app.db.database import db
from app.models import (
    AIDayScheduleRequest,
    AIImageTaskRequest,
    AIJob,
    AIJobStatus,
    AITaskRequest,
    AgentRunRequest,
    ToolDefinitionSchema,
)
from app.models.schemas import AgentRunMode, AgentRunResponse
from app.services.ai_service import AIService
from app.services.tool_registry import task_tool_registry


ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post("/agent/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    job = AgentRuntime.create_job()
    await AgentRuntime.run(job.job_id, request)
    return AgentRuntime.get_response(job.job_id)


@ai_router.get("/agent/runs/{job_id}", response_model=AgentRunResponse)
async def get_agent_run(job_id: str):
    try:
        return AgentRuntime.get_response(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Agent run not found.") from exc


@ai_router.post("/agent/runs/{job_id}/confirm", response_model=AgentRunResponse)
async def confirm_agent_run(job_id: str):
    try:
        AgentRuntime.confirm(job_id)
        return AgentRuntime.get_response(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Agent run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@ai_router.get("/agent/tools", response_model=list[ToolDefinitionSchema])
async def list_agent_tools():
    return [definition.to_schema() for definition in task_tool_registry.list_tools()]


@ai_router.post("/plan-tasks/async")
async def ai_plan_tasks_async(request: AITaskRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    job = AIJob(job_id=job_id, status=AIJobStatus.PENDING, created_at=datetime.now())
    db.create_ai_job(job)

    max_tasks = max(1, min(10, request.max_tasks))
    background_tasks.add_task(AIService.process_task_planning, job_id, request.prompt, max_tasks)

    return {
        "job_id": job_id,
        "status": "processing",
        "max_tasks": max_tasks,
        "message": f"Planning {max_tasks} tasks from the provided goal.",
    }


@ai_router.post("/plan-image/async")
async def ai_plan_image_async(background_tasks: BackgroundTasks, request: AIImageTaskRequest):
    image_bytes = _decode_and_validate_image(
        image_base64=request.image_base64,
        content_type=request.image_mime_type,
    )

    job_id = str(uuid4())
    job = AIJob(job_id=job_id, status=AIJobStatus.PENDING, created_at=datetime.now())
    db.create_ai_job(job)

    background_tasks.add_task(
        AIService.process_image_task_planning,
        job_id,
        image_bytes=image_bytes,
        image_mime_type=request.image_mime_type,
        filename=request.filename or "upload-image",
        notes=request.notes,
        max_tasks=max(0, min(10, request.max_tasks)),
        auto_create=request.auto_create,
    )
    return {
        "job_id": job_id,
        "status": "processing",
        "max_tasks": max(0, min(10, request.max_tasks)),
        "auto_create": request.auto_create,
        "message": "Processing the uploaded image for task extraction.",
    }


@ai_router.get("/jobs/{job_id}")
async def get_ai_job_status(job_id: str):
    job = db.get_ai_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@ai_router.post("/schedule-day/async")
async def ai_schedule_day_async(
    request: AIDayScheduleRequest,
    background_tasks: BackgroundTasks,
    force_regenerate: bool = False,
):
    job_id = str(uuid4())
    job = AIJob(job_id=job_id, status=AIJobStatus.PENDING, created_at=datetime.now())
    db.create_ai_job(job)
    background_tasks.add_task(
        AIService.process_day_schedule,
        job_id,
        request.date,
        request.task_ids,
        force_regenerate,
    )
    return {"job_id": job_id, "status": "processing"}


@ai_router.get("/schedule/{date}")
async def get_day_schedule(date: str):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc

    schedule = db.get_day_schedule(date)
    if not schedule:
        return {"date": date, "has_schedule": False, "schedule": None, "tasks_changed": False}

    from app.agent.planner import AgentPlanner

    current_tasks = db.get_tasks_for_date(target_date)
    current_version = AgentPlanner.generate_task_version(current_tasks)
    return {
        "date": date,
        "has_schedule": True,
        "schedule": schedule,
        "tasks_changed": schedule.task_version != current_version,
    }


@ai_router.delete("/schedule/{date}")
async def delete_day_schedule(date: str):
    success = db.delete_day_schedule(date)
    if not success:
        raise HTTPException(status_code=404, detail="No saved schedule exists for this date.")
    return {"message": "Schedule deleted."}


@ai_router.get("/schedule-day/{date}")
async def get_day_schedule_preview(date: str):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc

    day_tasks = db.get_tasks_for_date(target_date)
    total_estimated_hours = sum(task.estimated_hours or 2.0 for task in day_tasks)
    high_priority_count = sum(1 for task in day_tasks if task.priority == "high")
    overdue_count = sum(
        1 for task in day_tasks if task.due_date and task.due_date < datetime.now()
    )

    return {
        "date": date,
        "task_count": len(day_tasks),
        "total_estimated_hours": total_estimated_hours,
        "high_priority_count": high_priority_count,
        "overdue_count": overdue_count,
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "priority": task.priority,
                "estimated_hours": task.estimated_hours or 2.0,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in day_tasks
        ],
    }


@ai_router.post("/plan-tasks/test")
async def test_ai_planning(prompt: str = "Learn React Native", max_tasks: int = 3):
    job = AgentRuntime.create_job()
    await AgentRuntime.run(
        job.job_id,
        AgentRunRequest(
            mode=AgentRunMode.TEXT_GOAL,
            prompt=prompt,
            max_tasks=max_tasks,
            auto_execute=True,
        ),
    )
    return AgentRuntime.get_response(job.job_id).model_dump(mode="json")


@ai_router.post("/plan-image/test")
async def test_ai_image_planning(request: AIImageTaskRequest):
    return await _run_image_planning_sync(request)


@ai_router.post("/plan-image/sync")
async def sync_ai_image_planning(request: AIImageTaskRequest):
    return await _run_image_planning_sync(request)


async def _run_image_planning_sync(request: AIImageTaskRequest):
    job = AgentRuntime.create_job()
    await AgentRuntime.run(
        job.job_id,
        AgentRunRequest(
            mode=AgentRunMode.IMAGE_GOAL,
            image_base64=request.image_base64,
            image_mime_type=request.image_mime_type,
            filename=request.filename or "upload-image",
            notes=request.notes,
            max_tasks=max(0, min(10, request.max_tasks)),
            auto_execute=request.auto_create,
        ),
    )
    response = AgentRuntime.get_response(job.job_id)
    stored_job = db.get_ai_job(response.job_id)
    return {
        "success": response.status in {AIJobStatus.AWAITING_CONFIRMATION, AIJobStatus.COMPLETED},
        "job_id": response.job_id,
        "requires_confirmation": response.requires_confirmation,
        "task_candidates": [candidate.model_dump(mode="json") for candidate in response.artifacts.task_candidates],
        "created_tasks": [task.model_dump(mode="json") for task in response.artifacts.created_tasks],
        "scene_summary": response.trace_summary.goal_summary,
        "trace": stored_job.trace.model_dump(mode="json") if stored_job and stored_job.trace else None,
        "error": response.error,
    }


def _decode_and_validate_image(*, image_base64: str, content_type: str | None) -> bytes:
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image payload.") from exc

    _validate_image_upload(content_type, len(image_bytes))
    return image_bytes


def _validate_image_upload(content_type: str | None, size_bytes: int) -> None:
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")

    max_bytes = current_settings.MAX_IMAGE_UPLOAD_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds the {current_settings.MAX_IMAGE_UPLOAD_MB}MB upload limit.",
        )
