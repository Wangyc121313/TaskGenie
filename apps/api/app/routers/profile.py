from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import (
    UserMemoryCreate,
    UserMemoryItem,
    UserMemoryUpdate,
    UserPlanningContext,
    UserPreferences,
    UserPreferencesUpdate,
)
from app.services.memory_service import MemoryService


profile_router = APIRouter(prefix="/profile", tags=["profile"])


@profile_router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences():
    return MemoryService.get_preferences()


@profile_router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(payload: UserPreferencesUpdate):
    return MemoryService.update_preferences(payload)


@profile_router.get("/memories", response_model=List[UserMemoryItem])
async def list_user_memories(category: Optional[str] = Query(default=None)):
    return MemoryService.list_memories(category=category)


@profile_router.post("/memories", response_model=UserMemoryItem)
async def create_user_memory(payload: UserMemoryCreate):
    return MemoryService.create_memory(payload)


@profile_router.put("/memories/{memory_id}", response_model=UserMemoryItem)
async def update_user_memory(memory_id: str, payload: UserMemoryUpdate):
    updated = MemoryService.update_memory(memory_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return updated


@profile_router.delete("/memories/{memory_id}")
async def delete_user_memory(memory_id: str):
    if not MemoryService.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"message": "Memory deleted."}


@profile_router.get("/planning-context", response_model=UserPlanningContext)
async def preview_planning_context(prompt: str):
    return MemoryService.build_planning_context(prompt=prompt)
