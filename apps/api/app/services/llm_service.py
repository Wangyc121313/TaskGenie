import base64
import json
import re
from typing import Iterable, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import current_settings
from app.models.schemas import ConversationTurn, ConversationSummaryResult


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LLMResponseError(RuntimeError):
    pass


class LLMService:
    _client = OpenAI(
        api_key=current_settings.OPENAI_API_KEY,
        base_url=current_settings.OPENAI_BASE_URL,
        timeout=current_settings.AI_RESPONSE_TIMEOUT,
    )

    @classmethod
    def generate_structured_output(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[ResponseModelT],
        temperature: float = 0.7,
        max_tokens: int = 1200,
    ) -> ResponseModelT:
        request_kwargs = {
            "model": current_settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = cls._client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            if not cls._should_retry_without_response_format(exc):
                raise
            fallback_kwargs = dict(request_kwargs)
            fallback_kwargs.pop("response_format", None)
            response = cls._client.chat.completions.create(**fallback_kwargs)

        content = response.choices[0].message.content or ""
        payload = cls._extract_json_payload(content)

        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise LLMResponseError(
                f"Model response did not match {response_model.__name__}: {exc}"
            ) from exc

    @classmethod
    def generate_multimodal_text(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        image_mime_type: str,
        temperature: float = 0.1,
        max_tokens: int = 1600,
    ) -> str:
        """Call the vision model and return plain text (no structured output parsing)."""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{image_mime_type};base64,{image_b64}"

        response = cls._client.chat.completions.create(
            model=current_settings.OPENAI_VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    @classmethod
    def generate_multimodal_structured_output(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        image_mime_type: str,
        response_model: Type[ResponseModelT],
        temperature: float = 0.4,
        max_tokens: int = 1600,
    ) -> ResponseModelT:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{image_mime_type};base64,{image_b64}"

        response = cls._client.chat.completions.create(
            model=current_settings.OPENAI_VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                            },
                        },
                    ],
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        payload = cls._extract_json_payload(content)

        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise LLMResponseError(
                f"Vision model response did not match {response_model.__name__}: {exc}"
            ) from exc

    @staticmethod
    def _extract_json_payload(content: str):
        code_fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if code_fence_match:
            candidate = code_fence_match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        object_start = content.find("{")
        object_end = content.rfind("}") + 1
        if object_start != -1 and object_end > object_start:
            try:
                return json.loads(content[object_start:object_end])
            except json.JSONDecodeError:
                pass

        array_start = content.find("[")
        array_end = content.rfind("]") + 1
        if array_start != -1 and array_end > array_start:
            try:
                return json.loads(content[array_start:array_end])
            except json.JSONDecodeError:
                pass

        raise LLMResponseError("Could not extract valid JSON from model response")

    @staticmethod
    def _should_retry_without_response_format(exc: Exception) -> bool:
        message = str(exc).lower()
        return "response_format" in message or "json_object" in message

    @classmethod
    def compress_running_summary(
        cls,
        *,
        title: str,
        existing_summary: str,
        recent_turns: Iterable[ConversationTurn],
    ) -> str:
        turns_payload = [
            {
                "user_message": turn.user_message,
                "goal_summary": turn.goal_summary,
                "agent_summary": turn.agent_summary,
                "status": turn.status.value,
                "created_task_count": turn.created_task_count,
            }
            for turn in recent_turns
        ]
        prompt = (
            f"Conversation title: {title}\n"
            f"Existing summary:\n{existing_summary or 'None'}\n\n"
            f"Recent turns:\n{json.dumps(turns_payload, ensure_ascii=False, indent=2)}"
        )
        result = cls.generate_structured_output(
            system_prompt=(
                "Summarize the conversation into one short paragraph for future planning context. "
                "Preserve the active goal, key constraints, user preferences, and current progress. "
                "Do not mention every turn verbatim."
            ),
            user_prompt=prompt,
            response_model=ConversationSummaryResult,
            temperature=0.2,
            max_tokens=300,
        )
        return result.summary.strip()
