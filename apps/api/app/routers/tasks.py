from typing import List

from fastapi import APIRouter, HTTPException

from app.models import Task, TaskCreate, TaskUpdate
from app.services.task_service import TaskService


task_router = APIRouter(prefix="/tasks", tags=["tasks"])


@task_router.post("", response_model=Task)
async def create_task(task: TaskCreate):
    return TaskService.create_task(task)


@task_router.get("", response_model=List[Task])
async def get_all_tasks():
    return TaskService.get_all_tasks()


@task_router.get("/by-tags")
async def get_tasks_by_tags(tags: str = ""):
    if not tags:
        return TaskService.get_all_tasks()

    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if not tag_list:
        return TaskService.get_all_tasks()

    return TaskService.get_tasks_by_tags(tag_list)


@task_router.get("/by-tag/{tag}")
async def get_tasks_by_tag(tag: str):
    return TaskService.get_tasks_by_tag(tag)


@task_router.get("/calendar/{year}/{month}")
async def get_calendar_tasks(year: int, month: int):
    return TaskService.get_calendar_tasks(year, month)


@task_router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@task_router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate):
    task = TaskService.update_task(task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@task_router.delete("/{task_id}")
async def delete_task(task_id: str):
    success = TaskService.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已删除"}
