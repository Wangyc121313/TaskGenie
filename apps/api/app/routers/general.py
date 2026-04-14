from fastapi import APIRouter

from app.models import TagsResponse, TaskStatsResponse
from app.services.tag_service import TagService
from app.services.task_service import TaskService


general_router = APIRouter(tags=["general"])


@general_router.get("/stats", response_model=TaskStatsResponse)
async def get_stats():
    return TaskService.get_task_stats()


@general_router.get("/tags", response_model=TagsResponse)
async def get_available_tags():
    return TagService.get_available_tags()
