import asyncio
from datetime import datetime

from app.agent import runtime as runtime_module
from app.agent.runtime import AgentRuntime
from app.models.schemas import AIJob, AIJobStatus, AgentExecutionStatus, AgentRunMode, AgentRunRequest


def test_agent_runtime_offloads_sync_path_to_threadpool(monkeypatch):
    threadpool_calls = []

    async def fake_run_in_threadpool(func, *args, **kwargs):
        threadpool_calls.append((func, args, kwargs))
        return func(*args, **kwargs)

    def fake_update_job(job_id, **kwargs):
        return AIJob(
            job_id=job_id,
            status=kwargs.get("status", AIJobStatus.PENDING),
            created_at=datetime.now(),
            result=kwargs.get("result"),
            error=kwargs.get("error"),
            trace=kwargs.get("trace"),
        )

    def fake_run_text_goal(*, job_id, request, trace):
        trace.execution_status = AgentExecutionStatus.COMPLETED
        return AIJob(
            job_id=job_id,
            status=AIJobStatus.COMPLETED,
            created_at=datetime.now(),
            trace=trace,
        )

    monkeypatch.setattr(runtime_module, "run_in_threadpool", fake_run_in_threadpool)
    monkeypatch.setattr(AgentRuntime, "_update_job", staticmethod(fake_update_job))
    monkeypatch.setattr(AgentRuntime, "_run_text_goal", staticmethod(fake_run_text_goal))

    result = asyncio.run(
        AgentRuntime.run(
            "runtime-threadpool-job",
            AgentRunRequest(
                mode=AgentRunMode.TEXT_GOAL,
                prompt="Implement the MCP bridge",
                auto_execute=True,
            ),
        )
    )

    assert result.status == AIJobStatus.COMPLETED
    assert len(threadpool_calls) == 1

