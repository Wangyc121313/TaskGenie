from types import SimpleNamespace

from app.services.llm_service import LLMService


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


def test_generate_structured_output_prefers_json_response_format(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse('{"goal_summary":"ok","project_theme":"Demo","success_criteria":[],"plan_rationale":"","risk_notes":[],"tasks":[]}')

    monkeypatch.setattr(LLMService._client.chat.completions, "create", fake_create)

    from app.models.schemas import AgentTaskPlanResult

    result = LLMService.generate_structured_output(
        system_prompt="system",
        user_prompt="user",
        response_model=AgentTaskPlanResult,
    )

    assert result.project_theme == "Demo"
    assert captured["response_format"] == {"type": "json_object"}


def test_generate_structured_output_falls_back_when_response_format_is_rejected(monkeypatch):
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("response_format is not supported")
        return _FakeResponse('{"goal_summary":"fallback","project_theme":"Fallback","success_criteria":[],"plan_rationale":"","risk_notes":[],"tasks":[]}')

    monkeypatch.setattr(LLMService._client.chat.completions, "create", fake_create)

    from app.models.schemas import AgentTaskPlanResult

    result = LLMService.generate_structured_output(
        system_prompt="system",
        user_prompt="user",
        response_model=AgentTaskPlanResult,
    )

    assert result.project_theme == "Fallback"
    assert calls[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in calls[1]
