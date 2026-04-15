import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.db.database import db
from app.models import AIDayScheduleRequest, AIJob, AIJobStatus, AITaskRequest
from app.services.ai_service import AIService


ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post("/plan-tasks/async")
async def ai_plan_tasks_async(request: AITaskRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
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


@ai_router.get("/jobs/{job_id}")
async def get_ai_job_status(job_id: str):
    job = db.get_ai_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@ai_router.post("/schedule-day/async")
async def ai_schedule_day_async(
    request: AIDayScheduleRequest,
    background_tasks: BackgroundTasks,
    force_regenerate: bool = False,
):
    job_id = str(uuid.uuid4())
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
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式") from exc

    schedule = db.get_day_schedule(date)
    if not schedule:
        return {"date": date, "has_schedule": False, "schedule": None, "tasks_changed": False}

    current_tasks = db.get_tasks_for_date(target_date)
    current_version = AIService._generate_task_version(current_tasks)
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
        raise HTTPException(status_code=404, detail="该日期没有安排")
    return {"message": "安排已删除"}


@ai_router.get("/schedule-day/{date}")
async def get_day_schedule_preview(date: str):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式") from exc

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
    job_id = str(uuid.uuid4())
    job = AIJob(job_id=job_id, status=AIJobStatus.PENDING, created_at=datetime.now())
    db.create_ai_job(job)

    try:
        await AIService.process_task_planning(job_id, prompt, max_tasks)
        job = db.get_ai_job(job_id)
        if not job:
            return {"success": False, "error": "作业未找到"}
        if job.status == AIJobStatus.COMPLETED:
            return {
                "success": True,
                "tasks_created": len(job.result) if job.result else 0,
                "tasks": job.result,
                "trace": job.trace.model_dump(mode="json") if job.trace else None,
            }
        return {"success": False, "error": job.error}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
