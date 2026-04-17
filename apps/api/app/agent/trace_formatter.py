from app.models.schemas import (
    AIJob,
    AgentExecutionStatus,
    AgentRunArtifacts,
    AgentRunMode,
    AgentRunResponse,
    AgentRunSummary,
    AgentStrategy,
)


def format_job_as_agent_response(job: AIJob) -> AgentRunResponse:
    result = job.result or {}
    trace = job.trace
    mode = AgentRunMode(result.get("mode", AgentRunMode.TEXT_GOAL))
    strategy = (
        trace.strategy
        if trace is not None
        else AgentStrategy(result.get("strategy", AgentStrategy.PLAN_EXECUTE))
    )

    artifacts = AgentRunArtifacts(
        project_theme=result.get("artifacts", {}).get("project_theme"),
        planned_tasks=result.get("artifacts", {}).get("planned_tasks", []),
        task_candidates=result.get("artifacts", {}).get("task_candidates", []),
        created_tasks=result.get("artifacts", {}).get("created_tasks", []),
        schedule=result.get("artifacts", {}).get("schedule"),
        suggestions=result.get("artifacts", {}).get("suggestions", []),
        success_criteria=result.get("artifacts", {}).get("success_criteria", []),
        risk_notes=result.get("artifacts", {}).get("risk_notes", []),
        improvement_notes=result.get("artifacts", {}).get("improvement_notes", []),
    )
    summary = AgentRunSummary(
        job_id=job.job_id,
        mode=mode,
        strategy=strategy,
        current_stage=trace.current_step if trace is not None else "unknown",
        final_status=job.status,
        requires_confirmation=trace.requires_confirmation if trace is not None else False,
        goal_summary=trace.goal_summary if trace is not None else result.get("goal_summary"),
        project_theme=trace.project_theme if trace is not None else artifacts.project_theme,
        planned_task_count=len(trace.planned_tasks) if trace is not None else len(artifacts.planned_tasks),
        candidate_task_count=len(trace.extracted_candidates) if trace is not None else len(artifacts.task_candidates),
        executed_tool_count=len([tool for tool in (trace.tool_calls if trace is not None else []) if tool.status == "completed"]),
        created_task_count=len(trace.created_tasks) if trace is not None else len(artifacts.created_tasks),
        used_memory_count=len(trace.relevant_memories) if trace is not None else 0,
        improvement_notes=trace.improvement_notes if trace is not None else artifacts.improvement_notes,
        timeline=trace.decision_trace if trace is not None else [],
    )
    return AgentRunResponse(
        job_id=job.job_id,
        mode=mode,
        status=job.status,
        strategy=strategy,
        requires_confirmation=summary.requires_confirmation,
        trace_summary=summary,
        artifacts=artifacts,
        final_result=result.get("final_result"),
        error=job.error,
    )


def normalize_trace_completion_status(status: AgentExecutionStatus) -> str:
    return status.value
