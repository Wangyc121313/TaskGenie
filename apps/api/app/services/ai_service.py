from app.agent.runtime import AgentRuntime
from app.models.schemas import AgentRunMode, AgentRunRequest


class AIService:
    @staticmethod
    async def process_task_planning(job_id: str, prompt: str, max_tasks: int):
        await AgentRuntime.run(
            job_id,
            AgentRunRequest(
                mode=AgentRunMode.TEXT_GOAL,
                prompt=prompt,
                max_tasks=max_tasks,
                auto_execute=True,
            ),
        )

    @staticmethod
    async def process_image_task_planning(
        job_id: str,
        *,
        image_bytes: bytes,
        image_mime_type: str,
        filename: str,
        notes: str,
        conversation_id: str | None = None,
        max_tasks: int,
        auto_create: bool,
    ):
        import base64

        await AgentRuntime.run(
            job_id,
            AgentRunRequest(
                mode=AgentRunMode.IMAGE_GOAL,
                image_base64=base64.b64encode(image_bytes).decode("utf-8"),
                image_mime_type=image_mime_type,
                filename=filename,
                notes=notes,
                conversation_id=conversation_id,
                max_tasks=max_tasks,
                auto_execute=auto_create,
            ),
        )

    @staticmethod
    async def process_day_schedule(
        job_id: str,
        date_str: str,
        task_ids=None,
        force_regenerate: bool = False,
        conversation_id: str | None = None,
    ):
        await AgentRuntime.run(
            job_id,
            AgentRunRequest(
                mode=AgentRunMode.SCHEDULE_DAY,
                date=date_str,
                task_ids=task_ids,
                conversation_id=conversation_id,
                force_regenerate=force_regenerate,
                auto_execute=True,
            ),
        )
