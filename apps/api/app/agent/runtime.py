import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.agent.executor import build_task_creation_tool_calls, execute_tool_calls
from app.agent.planner import AgentPlanner
from app.agent.policy import should_require_confirmation
from app.agent.trace_formatter import format_job_as_agent_response
from app.db.database import db
from app.core.logging_utils import log_agent_event
from app.models.schemas import (
    AIJob,
    AIJobStatus,
    ConversationTurnStatus,
    AgentDecisionStatus,
    AgentDecisionTrace,
    AgentExecutionStatus,
    AgentRunMode,
    AgentRunRequest,
    AgentTraceEvent,
    AgentToolCallTrace,
    DaySchedule,
    PlannedTask,
    Task,
    AgentTaskPlanResult,
    TaskPlanningTrace,
)
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.tool_registry import task_tool_registry


class AgentRuntime:
    @staticmethod
    async def run(job_id: str, request: AgentRunRequest) -> AIJob:
        trace = TaskPlanningTrace(
            trace_id=str(uuid.uuid4()),
            current_step="analyzing",
            execution_status=AgentExecutionStatus.PLANNING,
            strategy="plan_execute",
            input_modality="image" if request.mode == AgentRunMode.IMAGE_GOAL else "text",
            started_at=datetime.now(),
        )
        log_agent_event(
            "agent_run_started",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            mode=request.mode.value,
        )
        AgentRuntime._update_job(job_id, status=AIJobStatus.PROCESSING, trace=trace, error=None)

        try:
            if request.mode == AgentRunMode.TEXT_GOAL:
                job = AgentRuntime._run_text_goal(job_id=job_id, request=request, trace=trace)
            elif request.mode == AgentRunMode.IMAGE_GOAL:
                job = AgentRuntime._run_image_goal(job_id=job_id, request=request, trace=trace)
            else:
                job = AgentRuntime._run_day_schedule(job_id=job_id, request=request, trace=trace)
        except Exception as exc:
            trace.execution_status = AgentExecutionStatus.FAILED
            trace.current_step = "failed"
            trace.finished_at = datetime.now()
            AgentRuntime._append_trace_event(
                trace,
                event_type="run_failed",
                stage="failure",
                message="The agent runtime failed.",
                metadata={"error": str(exc)},
            )
            AgentRuntime._append_decision(
                trace,
                stage="failure",
                decision="Fail the run",
                action="Persist failure state",
                observation=str(exc),
                status=AgentDecisionStatus.FAILED,
            )
            log_agent_event(
                "agent_run_failed",
                job_id=job_id,
                trace_id=trace.trace_id,
                strategy=trace.strategy.value,
                current_step=trace.current_step,
                error=str(exc),
            )
            AgentRuntime._upsert_conversation_turn(
                trace=trace,
                job_id=job_id,
                status=ConversationTurnStatus.FAILED,
            )
            return AgentRuntime._update_job(
                job_id,
                status=AIJobStatus.FAILED,
                trace=trace,
                error=str(exc),
            )

        return job

    @staticmethod
    def confirm(job_id: str) -> AIJob:
        job = db.get_ai_job(job_id)
        if not job:
            raise KeyError("Agent run not found.")
        if job.status != AIJobStatus.AWAITING_CONFIRMATION or job.trace is None:
            raise ValueError("This agent run does not require confirmation.")

        trace = job.trace
        trace.current_step = "executing"
        trace.execution_status = AgentExecutionStatus.EXECUTING
        AgentRuntime._append_trace_event(
            trace,
            event_type="execution_started",
            stage="execution",
            message="Started executing confirmed tool calls.",
            metadata={"tool_call_count": len(trace.tool_calls)},
        )
        AgentRuntime._append_trace_event(
            trace,
            event_type="confirmation_received",
            stage="policy",
            message="User confirmed execution of pending tool calls.",
        )
        log_agent_event(
            "agent_confirmation_received",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            tool_call_count=len(trace.tool_calls),
        )
        AgentRuntime._append_decision(
            trace,
            stage="policy",
            decision="Allow side-effecting execution",
            action="Run confirmed tool calls",
            observation=f"{len(trace.tool_calls)} tool calls ready",
        )
        AgentRuntime._update_job(job_id, status=AIJobStatus.PROCESSING, trace=trace, error=None)

        created_tasks = execute_tool_calls(
            trace.tool_calls,
            on_step=lambda index, tool_call, result, error: AgentRuntime._record_tool_step(
                job_id=job_id,
                trace=trace,
                index=index,
                tool_call=tool_call,
                result=result,
                error=error,
            ),
        )
        trace.created_tasks = [task for task in created_tasks if isinstance(task, Task)]
        trace.execution_status = AgentExecutionStatus.COMPLETED
        trace.current_step = "completed"
        trace.requires_confirmation = False
        trace.finished_at = datetime.now()
        AgentRuntime._append_reflection_for_completion(trace)
        AgentRuntime._append_trace_event(
            trace,
            event_type="run_completed",
            stage="completion",
            message="Completed the confirmed agent execution.",
            metadata={"created_task_count": len(trace.created_tasks)},
        )
        log_agent_event(
            "agent_run_completed",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            created_task_count=len(trace.created_tasks),
        )
        AgentRuntime._append_decision(
            trace,
            stage="completion",
            decision="Finalize run",
            action="Persist confirmed result",
            observation=f"Created {len(trace.created_tasks)} tasks",
        )
        result_payload = job.result or {}
        result_payload["artifacts"]["created_tasks"] = [
            task.model_dump(mode="json") for task in trace.created_tasks
        ]
        result_payload["final_result"] = {
            "created_tasks": [task.model_dump(mode="json") for task in trace.created_tasks]
        }
        AgentRuntime._upsert_conversation_turn(
            trace=trace,
            job_id=job_id,
            status=ConversationTurnStatus.COMPLETED,
        )
        return AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.COMPLETED,
            trace=trace,
            result=result_payload,
            error=None,
        )

    @staticmethod
    def _run_text_goal(*, job_id: str, request: AgentRunRequest, trace: TaskPlanningTrace) -> AIJob:
        if not request.prompt:
            raise ValueError("Prompt is required for text_goal mode.")

        prompt = request.prompt.strip()
        trace.source_prompt = prompt
        now = datetime.now()
        conversation = ConversationService.get_or_create_conversation(
            request.conversation_id,
            initial_prompt=prompt,
        )
        trace.conversation_id = conversation.conversation_id
        trace.conversation_turn_count = len(conversation.turns)
        conversation_context = ConversationService.build_context(conversation)
        trace.conversation_summary = conversation.running_summary
        planning_context = MemoryService.build_planning_context(prompt=prompt)
        trace.task_type = AgentPlanner.analyze_task_type(prompt)
        trace.preference_snapshot = planning_context.preferences
        trace.relevant_memories = planning_context.relevant_memories
        trace.behavior_summary = planning_context.behavior_summary
        AgentRuntime._append_trace_event(
            trace,
            event_type="memory_loaded",
            stage="context",
            message="Loaded user preferences and relevant memories.",
            metadata={"memory_count": len(planning_context.relevant_memories)},
        )
        log_agent_event(
            "agent_memory_loaded",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            used_memory_count=len(planning_context.relevant_memories),
        )
        AgentRuntime._append_decision(
            trace,
            stage="analyze",
            decision="Use plan-and-execute strategy",
            action="Build text planning context",
            observation=f"Matched {len(planning_context.relevant_memories)} memories",
        )
        combined_planning_context = planning_context.prompt_context
        if conversation_context:
            combined_planning_context = f"{combined_planning_context}\n\n{conversation_context}".strip()

        if request.auto_execute:
            return AgentRuntime._run_text_goal_iteratively(
                job_id=job_id,
                request=request,
                trace=trace,
                prompt=prompt,
                planning_context=combined_planning_context,
            )

        trace.current_step = "planning"
        planning_started = time.perf_counter()
        plan = AgentPlanner.plan_text_goal(
            prompt=prompt,
            max_tasks=max(1, min(10, request.max_tasks)),
            now=now,
            planning_context=combined_planning_context,
        )
        planning_latency_ms = int((time.perf_counter() - planning_started) * 1000)
        trace.goal_summary = plan.goal_summary
        trace.project_theme = plan.project_theme
        trace.planned_tasks = plan.tasks
        trace.success_criteria = plan.success_criteria
        trace.plan_rationale = plan.plan_rationale
        trace.risk_notes = plan.risk_notes
        AgentRuntime._append_trace_event(
            trace,
            event_type="planning_completed",
            stage="planning",
            message="Generated a structured task plan.",
            metadata={
                "project_theme": plan.project_theme,
                "planned_task_count": len(plan.tasks),
                "latency_ms": planning_latency_ms,
            },
        )
        AgentRuntime._append_decision(
            trace,
            stage="planning",
            decision="Produce executable plan",
            action="Generate structured tasks and rationale",
            observation=f"Generated {len(plan.tasks)} tasks",
            latency_ms=planning_latency_ms,
        )

        trace.tool_calls = build_task_creation_tool_calls(
            planned_tasks=plan.tasks,
            project_theme=plan.project_theme,
            max_tasks=max(1, min(10, request.max_tasks)),
            now=now,
        )
        trace.requires_confirmation = should_require_confirmation(
            trace.tool_calls,
            auto_execute=request.auto_execute,
        )
        AgentRuntime._append_trace_event(
            trace,
            event_type="execution_plan_created",
            stage="execution",
            message="Converted the plan into internal tool calls.",
            metadata={"tool_call_count": len(trace.tool_calls)},
        )
        AgentRuntime._append_decision(
            trace,
            stage="execution_plan",
            decision="Prepare tool execution",
            action="Translate tasks into tool calls",
            observation=f"{len(trace.tool_calls)} tool calls prepared",
        )

        trace.improvement_notes = AgentPlanner.reflect_text_plan(plan)
        AgentRuntime._append_decision(
            trace,
            stage="reflection",
            decision="Review plan quality",
            action="Generate lightweight reflection notes",
            observation=f"{len(trace.improvement_notes)} improvement notes",
        )

        result_payload = {
            "mode": request.mode.value,
            "strategy": trace.strategy.value,
            "goal_summary": trace.goal_summary,
            "artifacts": {
                "project_theme": trace.project_theme,
                "planned_tasks": [task.model_dump(mode="json") for task in trace.planned_tasks],
                "created_tasks": [],
                "success_criteria": trace.success_criteria,
                "risk_notes": trace.risk_notes,
                "improvement_notes": trace.improvement_notes,
            },
            "final_result": None,
        }

        if trace.requires_confirmation:
            trace.execution_status = AgentExecutionStatus.PENDING
            trace.current_step = "awaiting_confirmation"
            AgentRuntime._append_trace_event(
                trace,
                event_type="confirmation_required",
                stage="policy",
                message="Execution paused for user confirmation.",
                metadata={"tool_call_count": len(trace.tool_calls)},
            )
            log_agent_event(
                "agent_confirmation_required",
                job_id=job_id,
                trace_id=trace.trace_id,
                strategy=trace.strategy.value,
                tool_call_count=len(trace.tool_calls),
            )
            AgentRuntime._upsert_conversation_turn(
                trace=trace,
                job_id=job_id,
                status=ConversationTurnStatus.AWAITING_CONFIRMATION,
            )
            return AgentRuntime._update_job(
                job_id,
                status=AIJobStatus.AWAITING_CONFIRMATION,
                trace=trace,
                result=result_payload,
                error=None,
            )

        trace.execution_status = AgentExecutionStatus.EXECUTING
        trace.current_step = "executing"
        AgentRuntime._append_trace_event(
            trace,
            event_type="execution_started",
            stage="execution",
            message="Started executing text-goal tool calls.",
            metadata={"tool_call_count": len(trace.tool_calls)},
        )
        created_tasks = execute_tool_calls(
            trace.tool_calls,
            on_step=lambda index, tool_call, result, error: AgentRuntime._record_tool_step(
                job_id=job_id,
                trace=trace,
                index=index,
                tool_call=tool_call,
                result=result,
                error=error,
            ),
        )
        trace.created_tasks = [task for task in created_tasks if isinstance(task, Task)]
        trace.execution_status = AgentExecutionStatus.COMPLETED
        trace.current_step = "completed"
        trace.finished_at = datetime.now()
        AgentRuntime._append_reflection_for_completion(trace)
        AgentRuntime._append_trace_event(
            trace,
            event_type="run_completed",
            stage="completion",
            message="Completed the text-goal agent run.",
            metadata={"created_task_count": len(trace.created_tasks)},
        )
        log_agent_event(
            "agent_run_completed",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            created_task_count=len(trace.created_tasks),
        )
        result_payload["artifacts"]["created_tasks"] = [
            task.model_dump(mode="json") for task in trace.created_tasks
        ]
        result_payload["final_result"] = {
            "created_tasks": [task.model_dump(mode="json") for task in trace.created_tasks]
        }
        AgentRuntime._upsert_conversation_turn(
            trace=trace,
            job_id=job_id,
            status=ConversationTurnStatus.COMPLETED,
        )
        return AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.COMPLETED,
            trace=trace,
            result=result_payload,
            error=None,
        )

    @staticmethod
    def _run_text_goal_iteratively(
        *,
        job_id: str,
        request: AgentRunRequest,
        trace: TaskPlanningTrace,
        prompt: str,
        planning_context: str,
    ) -> AIJob:
        max_tasks = max(1, min(10, request.max_tasks))
        max_iterations = min(max_tasks + 1, 6)
        execution_history: list[dict[str, Any]] = []
        available_tools = AgentRuntime._serialize_available_tools()
        completion_message: Optional[str] = None

        for iteration in range(max_iterations):
            trace.current_step = "planning"
            AgentRuntime._append_trace_event(
                trace,
                event_type="planning_iteration_started",
                stage="planning",
                message="Started an iterative planning step.",
                metadata={"iteration": iteration + 1},
            )
            planning_started = time.perf_counter()
            step = AgentPlanner.plan_text_goal_step(
                prompt=prompt,
                now=datetime.now(),
                planning_context=planning_context,
                available_tools=available_tools,
                execution_history=[dict(item) for item in execution_history],
                max_tasks=max_tasks,
            )
            planning_latency_ms = int((time.perf_counter() - planning_started) * 1000)

            trace.goal_summary = step.goal_summary
            trace.project_theme = step.project_theme
            trace.success_criteria = step.success_criteria
            trace.plan_rationale = step.plan_rationale
            trace.risk_notes = step.risk_notes

            if step.is_complete:
                completion_message = step.completion_message
                AgentRuntime._append_trace_event(
                    trace,
                    event_type="planning_completed",
                    stage="planning",
                    message="Planner decided the goal is sufficiently advanced.",
                    metadata={
                        "iteration": iteration + 1,
                        "is_complete": True,
                        "latency_ms": planning_latency_ms,
                    },
                )
                AgentRuntime._append_decision(
                    trace,
                    stage="planning",
                    decision="Stop the iterative loop",
                    action="Finish without another tool call",
                    observation=step.completion_message or "Planner marked the run complete.",
                    latency_ms=planning_latency_ms,
                    metadata={"iteration": iteration + 1},
                )
                break

            if step.planned_task is None or step.tool_call is None:
                raise ValueError("Iterative text planning must return both planned_task and tool_call.")

            trace.planned_tasks.append(step.planned_task)
            tool_call = AgentRuntime._build_tool_call_trace(
                step.tool_call.tool_name,
                step.tool_call.arguments,
            )
            trace.tool_calls.append(tool_call)
            AgentRuntime._append_trace_event(
                trace,
                event_type="planning_completed",
                stage="planning",
                message="Planner produced the next tool-driven action.",
                metadata={
                    "iteration": iteration + 1,
                    "tool_name": tool_call.tool_name,
                    "latency_ms": planning_latency_ms,
                },
            )
            AgentRuntime._append_decision(
                trace,
                stage="planning",
                decision="Choose the next tool action",
                action=f"Queue {tool_call.tool_name}",
                observation=step.planned_task.name,
                latency_ms=planning_latency_ms,
                metadata={"iteration": iteration + 1},
            )

            trace.execution_status = AgentExecutionStatus.EXECUTING
            trace.current_step = "executing"
            AgentRuntime._append_trace_event(
                trace,
                event_type="execution_started",
                stage="execution",
                message="Started executing the planned tool call.",
                metadata={"iteration": iteration + 1, "tool_name": tool_call.tool_name},
            )
            results = execute_tool_calls(
                [tool_call],
                on_step=lambda index, current_tool_call, result, error: AgentRuntime._record_tool_step(
                    job_id=job_id,
                    trace=trace,
                    index=index,
                    tool_call=current_tool_call,
                    result=result,
                    error=error,
                ),
            )
            new_tasks = [result for result in results if isinstance(result, Task)]
            trace.created_tasks.extend(new_tasks)
            execution_history.append(
                {
                    "iteration": iteration + 1,
                    "tool_name": tool_call.tool_name,
                    "status": tool_call.status,
                    "output": tool_call.output,
                    "error": tool_call.error,
                }
            )

            if len(trace.created_tasks) >= max_tasks:
                AgentRuntime._append_decision(
                    trace,
                    stage="policy",
                    decision="Stop after reaching task limit",
                    action="End iterative execution",
                    observation=f"Created {len(trace.created_tasks)} tasks",
                    status=AgentDecisionStatus.SKIPPED,
                    metadata={"iteration": iteration + 1},
                )
                break

        if trace.planned_tasks:
            trace.improvement_notes = AgentPlanner.reflect_text_plan(
                AgentTaskPlanResult(
                    goal_summary=trace.goal_summary or "",
                    project_theme=trace.project_theme or "",
                    success_criteria=trace.success_criteria,
                    plan_rationale=trace.plan_rationale,
                    risk_notes=trace.risk_notes,
                    tasks=trace.planned_tasks,
                )
            )
        else:
            trace.improvement_notes = [
                "The loop finished without creating tasks; review whether the goal needed direct execution."
            ]

        trace.execution_status = AgentExecutionStatus.COMPLETED
        trace.current_step = "completed"
        trace.finished_at = datetime.now()
        AgentRuntime._append_reflection_for_completion(trace)
        AgentRuntime._append_trace_event(
            trace,
            event_type="run_completed",
            stage="completion",
            message="Completed the iterative text-goal agent run.",
            metadata={
                "created_task_count": len(trace.created_tasks),
                "completion_message": completion_message,
            },
        )
        log_agent_event(
            "agent_run_completed",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            created_task_count=len(trace.created_tasks),
        )
        result_payload = {
            "mode": request.mode.value,
            "strategy": trace.strategy.value,
            "goal_summary": trace.goal_summary,
            "artifacts": {
                "project_theme": trace.project_theme,
                "planned_tasks": [task.model_dump(mode="json") for task in trace.planned_tasks],
                "created_tasks": [task.model_dump(mode="json") for task in trace.created_tasks],
                "success_criteria": trace.success_criteria,
                "risk_notes": trace.risk_notes,
                "improvement_notes": trace.improvement_notes,
            },
            "final_result": {
                "created_tasks": [task.model_dump(mode="json") for task in trace.created_tasks],
                "completion_message": completion_message,
            },
        }
        AgentRuntime._upsert_conversation_turn(
            trace=trace,
            job_id=job_id,
            status=ConversationTurnStatus.COMPLETED,
        )
        return AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.COMPLETED,
            trace=trace,
            result=result_payload,
            error=None,
        )

    @staticmethod
    def _run_image_goal(*, job_id: str, request: AgentRunRequest, trace: TaskPlanningTrace) -> AIJob:
        if not request.image_base64:
            raise ValueError("image_base64 is required for image_goal mode.")

        from app.routers.ai import _decode_and_validate_image

        prompt = (request.notes or request.filename or "image-input").strip()
        trace.source_prompt = prompt
        conversation = ConversationService.get_or_create_conversation(
            request.conversation_id,
            initial_prompt=prompt,
        )
        trace.conversation_id = conversation.conversation_id
        trace.conversation_turn_count = len(conversation.turns)
        trace.conversation_summary = conversation.running_summary
        conversation_context = ConversationService.build_context(conversation)
        image_bytes = _decode_and_validate_image(
            image_base64=request.image_base64,
            content_type=request.image_mime_type,
        )
        planning_context = MemoryService.build_planning_context(
            prompt=prompt
        )
        trace.preference_snapshot = planning_context.preferences
        trace.relevant_memories = planning_context.relevant_memories
        trace.behavior_summary = planning_context.behavior_summary
        AgentRuntime._append_trace_event(
            trace,
            event_type="image_received",
            stage="input",
            message="Received an image input for agent planning.",
            metadata={"filename": request.filename, "mime_type": request.image_mime_type},
        )
        log_agent_event(
            "agent_image_received",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            filename=request.filename,
        )
        extraction = AgentPlanner.extract_image_tasks(
            image_bytes=image_bytes,
            image_mime_type=request.image_mime_type,
            filename=request.filename or "upload-image",
            notes=request.notes,
            max_tasks=max(0, min(10, request.max_tasks)),
            planning_context=AgentRuntime._merge_planning_contexts(
                planning_context.prompt_context,
                conversation_context,
            ),
        )
        trace.goal_summary = extraction.scene_summary
        trace.project_theme = extraction.detected_context
        trace.source_summary = extraction.scene_summary
        trace.extracted_candidates = extraction.tasks
        trace.planned_tasks = [
            PlannedTask(
                name=candidate.name,
                description=candidate.description,
                priority=candidate.priority,
                estimated_hours=candidate.estimated_hours,
                due_date=candidate.due_date,
            )
            for candidate in extraction.tasks
        ]
        trace.improvement_notes = AgentPlanner.reflect_image_tasks(extraction)
        trace.tool_calls = build_task_creation_tool_calls(
            planned_tasks=trace.planned_tasks,
            project_theme=extraction.detected_context or "Image Tasks",
            max_tasks=max(0, min(10, request.max_tasks)),
            now=datetime.now(),
        )
        trace.requires_confirmation = should_require_confirmation(
            trace.tool_calls,
            auto_execute=request.auto_execute,
        )
        AgentRuntime._append_decision(
            trace,
            stage="planning",
            decision="Extract candidates from image",
            action="Produce task candidates and source snippets",
            observation=f"Extracted {len(trace.extracted_candidates)} candidates",
        )

        result_payload = {
            "mode": request.mode.value,
            "strategy": trace.strategy.value,
            "goal_summary": trace.goal_summary,
            "artifacts": {
                "project_theme": trace.project_theme,
                "task_candidates": [candidate.model_dump(mode="json") for candidate in trace.extracted_candidates],
                "planned_tasks": [task.model_dump(mode="json") for task in trace.planned_tasks],
                "created_tasks": [],
                "improvement_notes": trace.improvement_notes,
            },
            "final_result": None,
        }
        if trace.requires_confirmation:
            trace.execution_status = AgentExecutionStatus.PENDING
            trace.current_step = "awaiting_confirmation"
            AgentRuntime._append_trace_event(
                trace,
                event_type="confirmation_required",
                stage="policy",
                message="Image-derived tasks are waiting for confirmation.",
                metadata={"candidate_count": len(trace.extracted_candidates)},
            )
            log_agent_event(
                "agent_confirmation_required",
                job_id=job_id,
                trace_id=trace.trace_id,
                strategy=trace.strategy.value,
                tool_call_count=len(trace.tool_calls),
            )
            AgentRuntime._upsert_conversation_turn(
                trace=trace,
                job_id=job_id,
                status=ConversationTurnStatus.AWAITING_CONFIRMATION,
            )
            return AgentRuntime._update_job(
                job_id,
                status=AIJobStatus.AWAITING_CONFIRMATION,
                trace=trace,
                result=result_payload,
                error=None,
            )

        trace.execution_status = AgentExecutionStatus.EXECUTING
        trace.current_step = "executing"
        AgentRuntime._append_trace_event(
            trace,
            event_type="execution_started",
            stage="execution",
            message="Started executing image-derived tool calls.",
            metadata={"tool_call_count": len(trace.tool_calls)},
        )
        created_tasks = execute_tool_calls(
            trace.tool_calls,
            on_step=lambda index, tool_call, result, error: AgentRuntime._record_tool_step(
                job_id=job_id,
                trace=trace,
                index=index,
                tool_call=tool_call,
                result=result,
                error=error,
            ),
        )
        trace.created_tasks = [task for task in created_tasks if isinstance(task, Task)]
        trace.execution_status = AgentExecutionStatus.COMPLETED
        trace.current_step = "completed"
        trace.finished_at = datetime.now()
        AgentRuntime._append_reflection_for_completion(trace)
        AgentRuntime._append_trace_event(
            trace,
            event_type="run_completed",
            stage="completion",
            message="Completed the image-goal agent run.",
            metadata={"created_task_count": len(trace.created_tasks)},
        )
        log_agent_event(
            "agent_run_completed",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            created_task_count=len(trace.created_tasks),
        )
        result_payload["artifacts"]["created_tasks"] = [
            task.model_dump(mode="json") for task in trace.created_tasks
        ]
        result_payload["final_result"] = {
            "created_tasks": [task.model_dump(mode="json") for task in trace.created_tasks]
        }
        AgentRuntime._upsert_conversation_turn(
            trace=trace,
            job_id=job_id,
            status=ConversationTurnStatus.COMPLETED,
        )
        return AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.COMPLETED,
            trace=trace,
            result=result_payload,
            error=None,
        )

    @staticmethod
    def _run_day_schedule(*, job_id: str, request: AgentRunRequest, trace: TaskPlanningTrace) -> AIJob:
        if not request.date:
            raise ValueError("date is required for schedule_day mode.")

        prompt = f"Build a schedule for {request.date}"
        trace.source_prompt = prompt
        conversation = ConversationService.get_or_create_conversation(
            request.conversation_id,
            initial_prompt=prompt,
        )
        trace.conversation_id = conversation.conversation_id
        trace.conversation_turn_count = len(conversation.turns)
        trace.conversation_summary = conversation.running_summary
        conversation_context = ConversationService.build_context(conversation)
        planning_context = MemoryService.build_planning_context(prompt=prompt)
        trace.preference_snapshot = planning_context.preferences
        trace.relevant_memories = planning_context.relevant_memories
        trace.behavior_summary = planning_context.behavior_summary

        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        schedule, regenerated = AgentPlanner.plan_day_schedule(
            target_date=target_date,
            task_ids=request.task_ids,
            force_regenerate=request.force_regenerate,
            planning_context=AgentRuntime._merge_planning_contexts(
                planning_context.prompt_context,
                conversation_context,
            ),
        )
        trace.goal_summary = f"Build an executable day schedule for {request.date}."
        trace.project_theme = f"Schedule {request.date}"
        trace.execution_status = AgentExecutionStatus.COMPLETED
        trace.current_step = "completed"
        trace.finished_at = datetime.now()
        trace.improvement_notes = [
            "Schedule quality improves when tasks include due dates and estimated hours."
        ]
        AgentRuntime._append_decision(
            trace,
            stage="planning",
            decision="Generate day schedule",
            action="Create or reuse a schedule for the requested date",
            observation="Reused existing schedule" if not regenerated else "Generated a fresh schedule",
        )
        result_payload = {
            "mode": request.mode.value,
            "strategy": trace.strategy.value,
            "goal_summary": trace.goal_summary,
            "artifacts": {
                "project_theme": trace.project_theme,
                "schedule": schedule.model_dump(mode="json"),
                "suggestions": schedule.suggestions,
                "improvement_notes": trace.improvement_notes,
            },
            "final_result": {
                "schedule": schedule.model_dump(mode="json"),
                "regenerated": regenerated,
            },
        }
        if regenerated:
            db.create_day_schedule(request.date, schedule)
        log_agent_event(
            "agent_schedule_completed",
            job_id=job_id,
            trace_id=trace.trace_id,
            strategy=trace.strategy.value,
            regenerated=regenerated,
            suggestion_count=len(schedule.suggestions),
        )
        AgentRuntime._upsert_conversation_turn(
            trace=trace,
            job_id=job_id,
            status=ConversationTurnStatus.COMPLETED,
        )
        return AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.COMPLETED,
            trace=trace,
            result=result_payload,
            error=None,
        )

    @staticmethod
    def create_job() -> AIJob:
        job_id = str(uuid.uuid4())
        job = AIJob(job_id=job_id, status=AIJobStatus.PENDING, created_at=datetime.now())
        return db.create_ai_job(job)

    @staticmethod
    def get_response(job_id: str):
        job = db.get_ai_job(job_id)
        if not job:
            raise KeyError("Agent run not found.")
        return format_job_as_agent_response(job)

    @staticmethod
    def _record_tool_step(
        *,
        job_id: str,
        trace: TaskPlanningTrace,
        index: int,
        tool_call,
        result: Optional[Any],
        error: Optional[Exception],
    ) -> None:
        if error is not None:
            trace.execution_status = AgentExecutionStatus.FAILED
            trace.current_step = "failed"
            AgentRuntime._append_trace_event(
                trace,
                event_type="tool_failed",
                stage="execution",
                message=f"Tool call {index + 1} failed.",
                metadata={
                    "tool_name": tool_call.tool_name,
                    "tool_index": index,
                    "error": str(error),
                },
            )
            AgentRuntime._append_decision(
                trace,
                stage="execution",
                decision="Stop execution",
                action=f"Abort on {tool_call.tool_name}",
                observation=str(error),
                status=AgentDecisionStatus.FAILED,
                latency_ms=tool_call.latency_ms,
            )
            log_agent_event(
                "agent_tool_failed",
                job_id=job_id,
                trace_id=trace.trace_id,
                tool_name=tool_call.tool_name,
                latency_ms=tool_call.latency_ms,
                error=str(error),
            )
        else:
            AgentRuntime._append_trace_event(
                trace,
                event_type="tool_completed",
                stage="execution",
                message=f"Tool call {index + 1} completed.",
                metadata={
                    "tool_name": tool_call.tool_name,
                    "tool_index": index,
                },
            )
            AgentRuntime._append_decision(
                trace,
                stage="execution",
                decision="Apply tool result",
                action=f"Run {tool_call.tool_name}",
                observation="Execution completed successfully",
                latency_ms=tool_call.latency_ms,
            )
            log_agent_event(
                "agent_tool_completed",
                job_id=job_id,
                trace_id=trace.trace_id,
                tool_name=tool_call.tool_name,
                latency_ms=tool_call.latency_ms,
            )
        AgentRuntime._update_job(
            job_id,
            status=AIJobStatus.PROCESSING if error is None else AIJobStatus.FAILED,
            trace=trace,
            error=str(error) if error is not None else None,
        )

    @staticmethod
    def _append_reflection_for_completion(trace: TaskPlanningTrace) -> None:
        AgentRuntime._append_decision(
            trace,
            stage="reflection",
            decision="Assess result quality",
            action="Summarize improvement notes after execution",
            observation=f"{len(trace.improvement_notes)} notes available",
            status=AgentDecisionStatus.COMPLETED,
        )

    @staticmethod
    def _append_trace_event(
        trace: TaskPlanningTrace,
        *,
        event_type: str,
        stage: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        trace.events.append(
            AgentTraceEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                stage=stage,
                message=message,
                metadata=metadata or {},
            )
        )

    @staticmethod
    def _serialize_available_tools() -> list[dict[str, Any]]:
        return [
            definition.to_schema().model_dump(mode="json")
            for definition in task_tool_registry.list_tools()
        ]

    @staticmethod
    def _merge_planning_contexts(memory_context: str, conversation_context: str) -> str:
        if not conversation_context:
            return memory_context
        return f"{memory_context}\n\n{conversation_context}".strip()

    @staticmethod
    def _build_tool_call_trace(tool_name: str, arguments: Dict[str, Any]) -> AgentToolCallTrace:
        definition = task_tool_registry.get_definition(tool_name)
        return AgentToolCallTrace(
            call_id=str(uuid.uuid4()),
            tool_name=definition.name,
            arguments=arguments,
            input_schema=definition.input_schema,
            output_schema=definition.output_schema,
            side_effect_level=definition.side_effect_level,
            requires_confirmation=definition.requires_confirmation,
            retryable=definition.retryable,
        )

    @staticmethod
    def _upsert_conversation_turn(
        *,
        trace: TaskPlanningTrace,
        job_id: str,
        status: ConversationTurnStatus,
    ) -> None:
        if not trace.conversation_id or not trace.source_prompt:
            return

        session = ConversationService.upsert_turn(
            conversation_id=trace.conversation_id,
            job_id=job_id,
            user_message=trace.source_prompt,
            goal_summary=trace.goal_summary,
            agent_summary=AgentRuntime._build_conversation_turn_summary(trace),
            status=status,
            created_task_count=len(trace.created_tasks),
        )
        trace.conversation_turn_count = len(session.turns)
        trace.conversation_summary = session.running_summary

    @staticmethod
    def _build_conversation_turn_summary(trace: TaskPlanningTrace) -> str:
        if trace.execution_status == AgentExecutionStatus.FAILED:
            return "The run failed before producing a stable result."
        if trace.created_tasks:
            return (
                f"{trace.goal_summary or 'Processed the user goal.'} "
                f"Created {len(trace.created_tasks)} task(s)."
            )
        if trace.current_step == "awaiting_confirmation":
            return (
                f"{trace.goal_summary or 'Processed the user goal.'} "
                f"Generated {len(trace.planned_tasks)} planned task(s) and is awaiting confirmation."
            )
        return trace.goal_summary or "Processed the user goal."

    @staticmethod
    def _append_decision(
        trace: TaskPlanningTrace,
        *,
        stage: str,
        decision: str,
        action: str,
        observation: str,
        status: AgentDecisionStatus = AgentDecisionStatus.COMPLETED,
        latency_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        trace.decision_trace.append(
            AgentDecisionTrace(
                timestamp=datetime.now(),
                stage=stage,
                decision=decision,
                action=action,
                observation=observation,
                status=status,
                latency_ms=latency_ms,
                metadata=metadata or {},
            )
        )

    @staticmethod
    def _update_job(
        job_id: str,
        *,
        status: AIJobStatus,
        trace: Optional[TaskPlanningTrace] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> AIJob:
        job = db.get_ai_job(job_id)
        if not job:
            raise KeyError("Agent job not found.")
        job.status = status
        if trace is not None:
            job.trace = trace
        if result is not None:
            job.result = result
        if error is not None or status != AIJobStatus.FAILED:
            job.error = error
        db.update_ai_job(job_id, job)
        return job
