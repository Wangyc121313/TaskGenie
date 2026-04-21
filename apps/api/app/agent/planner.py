import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.db.database import db
from app.models.schemas import (
    AgentTextPlanningStep,
    AgentTaskPlanResult,
    DaySchedule,
    DayScheduleGenerationResult,
    ImageTaskExtractionResult,
    PlannedTask,
    Task,
    TaskScheduleItem,
)
from app.services.llm_service import LLMService


class AgentPlanner:
    _TASK_TYPE_SIGNALS = {
        "development": {
            "phrases": {
                "implement": 4,
                "build": 3,
                "develop": 3,
                "design": 2,
                "refactor": 3,
                "debug": 3,
                "fix": 3,
                "ship": 2,
                "api": 1,
                "frontend": 1,
                "backend": 1,
                "feature": 1,
                "实现": 4,
                "开发": 3,
                "设计": 2,
                "重构": 3,
                "修复": 3,
                "接口": 1,
                "功能": 1,
            }
        },
        "learning": {
            "phrases": {
                "learn": 4,
                "study": 4,
                "research": 3,
                "understand": 2,
                "read": 2,
                "course": 2,
                "tutorial": 2,
                "学习": 4,
                "研究": 3,
                "理解": 2,
                "阅读": 2,
                "课程": 2,
            }
        },
        "planning": {
            "phrases": {
                "plan": 4,
                "organize": 3,
                "arrange": 3,
                "schedule": 4,
                "roadmap": 2,
                "prioritize": 2,
                "timeline": 2,
                "calendar": 2,
                "计划": 4,
                "安排": 4,
                "排期": 4,
                "时间块": 3,
                "时间表": 3,
                "日程": 3,
            }
        },
        "writing": {
            "phrases": {
                "write": 4,
                "draft": 4,
                "document": 3,
                "documentation": 3,
                "blog": 2,
                "essay": 2,
                "proposal": 2,
                "readme": 2,
                "docs": 2,
                "写": 4,
                "撰写": 4,
                "文档": 3,
                "说明": 2,
                "博客": 2,
                "简历": 2,
            }
        },
    }

    @staticmethod
    def analyze_task_type(prompt: str) -> str:
        normalized_prompt = prompt.lower().strip()
        if not normalized_prompt:
            return "general"

        scores = {task_type: 0 for task_type in AgentPlanner._TASK_TYPE_SIGNALS}
        for task_type, config in AgentPlanner._TASK_TYPE_SIGNALS.items():
            for phrase, weight in config["phrases"].items():
                if phrase in normalized_prompt:
                    scores[task_type] += weight

        strongest_match = max(scores.values())
        if strongest_match <= 0:
            return "general"

        top_task_types = [task_type for task_type, score in scores.items() if score == strongest_match]
        priority_order = ["planning", "development", "learning", "writing"]
        for task_type in priority_order:
            if task_type in top_task_types:
                return task_type

        return top_task_types[0]

    @staticmethod
    def plan_text_goal(
        *,
        prompt: str,
        max_tasks: int,
        now: datetime,
        planning_context: str,
    ) -> AgentTaskPlanResult:
        return LLMService.generate_structured_output(
            system_prompt=AgentPlanner._build_text_planner_prompt(
                max_tasks=max_tasks,
                now=now,
                planning_context=planning_context,
            ),
            user_prompt=f"User goal:\n{prompt}",
            response_model=AgentTaskPlanResult,
            temperature=0.5,
            max_tokens=1800,
        )

    @staticmethod
    def plan_text_goal_step(
        *,
        prompt: str,
        now: datetime,
        planning_context: str,
        available_tools: List[Dict[str, Any]],
        execution_history: List[Dict[str, Any]],
        max_tasks: int,
    ) -> AgentTextPlanningStep:
        return LLMService.generate_structured_output(
            system_prompt=AgentPlanner._build_text_loop_prompt(
                now=now,
                planning_context=planning_context,
                available_tools=available_tools,
                execution_history=execution_history,
                max_tasks=max_tasks,
            ),
            user_prompt=f"User goal:\n{prompt}",
            response_model=AgentTextPlanningStep,
            temperature=0.4,
            max_tokens=1200,
        )

    @staticmethod
    def reflect_text_plan(plan: AgentTaskPlanResult) -> List[str]:
        notes: List[str] = []
        if len(plan.tasks) <= 1:
            notes.append("The plan may be too coarse; consider splitting the goal into more intermediate tasks.")
        if all(task.priority != "high" for task in plan.tasks):
            notes.append("No task was marked high priority; verify whether the critical path is explicit enough.")
        if any(task.due_date is None for task in plan.tasks):
            notes.append("Some tasks do not have due dates; scheduling quality may improve after adding deadlines.")
        if not plan.success_criteria:
            notes.append("Success criteria are minimal; define what a finished outcome should look like.")
        return notes

    @staticmethod
    def _build_transcription_system_prompt() -> str:
        return (
            "You are a precise content-extraction assistant. "
            "Your only job is to faithfully transcribe or describe everything visible in the image.\n"
            "Rules:\n"
            "- If the image contains text (notes, lists, whiteboards, documents, code, screenshots): "
            "transcribe every word exactly as written, preserving structure and line breaks.\n"
            "- If the image shows diagrams, charts, or visual layouts: describe their structure, "
            "labels, and relationships in detail.\n"
            "- If the image shows both text and visuals, handle both.\n"
            "- Do NOT suggest tasks, interpret goals, draw conclusions, or add any commentary.\n"
            "- Return only plain text that mirrors the image content. No JSON, no markdown headers."
        )

    @staticmethod
    def transcribe_image_to_text(
        *,
        image_bytes: bytes,
        image_mime_type: str,
        filename: str,
    ) -> str:
        """Stage 1 of the 2-stage pipeline: use the vision model purely as a transcriber.

        The vision model extracts/describes raw image content without any task reasoning.
        The resulting text is fed to the text LLM in Stage 2 for structured task planning.
        """
        user_prompt = (
            f"Image filename: {filename}\n"
            "请将此图片中的全部内容完整提取出来（文字原样逐字转录；图表请详细描述结构和标签）。"
        )
        return LLMService.generate_multimodal_text(
            system_prompt=AgentPlanner._build_transcription_system_prompt(),
            user_prompt=user_prompt,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            temperature=0.1,
            max_tokens=1600,
        )

    @staticmethod
    def extract_image_tasks(
        *,
        image_bytes: bytes,
        image_mime_type: str,
        filename: str,
        notes: str,
        max_tasks: int,
        planning_context: str,
    ) -> ImageTaskExtractionResult:
        return LLMService.generate_multimodal_structured_output(
            system_prompt=AgentPlanner._build_image_task_system_prompt(
                max_tasks=max_tasks,
                planning_context=planning_context,
            ),
            user_prompt=AgentPlanner._build_image_task_user_prompt(
                filename=filename,
                notes=notes,
            ),
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            response_model=ImageTaskExtractionResult,
            temperature=0.3,
            max_tokens=1600,
        )

    @staticmethod
    def extract_tasks_from_transcription(
        *,
        transcription_text: str,
        filename: str,
        notes: str,
        max_tasks: int,
        planning_context: str,
    ) -> ImageTaskExtractionResult:
        """Stage 2 of the 2-stage pipeline: text LLM structures transcribed content into tasks."""
        user_prompt = f"Image filename: {filename}\n"
        if notes.strip():
            user_prompt += f"User notes:\n{notes.strip()}\n"
        user_prompt += f"Transcribed image content:\n{transcription_text}\n"
        user_prompt += "Extract actionable tasks from the content above."

        return LLMService.generate_structured_output(
            system_prompt=AgentPlanner._build_image_task_system_prompt(
                max_tasks=max_tasks,
                planning_context=planning_context,
            ),
            user_prompt=user_prompt,
            response_model=ImageTaskExtractionResult,
            temperature=0.3,
            max_tokens=1600,
        )

    @staticmethod
    def reflect_image_tasks(extraction_result: ImageTaskExtractionResult) -> List[str]:
        notes: List[str] = []
        if not extraction_result.tasks:
            notes.append("No actionable tasks were extracted; the image may need clearer text or more context notes.")
        if extraction_result.warnings:
            notes.extend(extraction_result.warnings)
        if any(candidate.confidence < 0.65 for candidate in extraction_result.tasks):
            notes.append("Some extracted tasks have low confidence and should be reviewed before creation.")
        return notes

    @staticmethod
    def plan_day_schedule(
        *,
        target_date: date,
        task_ids: Optional[List[str]],
        force_regenerate: bool,
        planning_context: str = "",
    ) -> Tuple[DaySchedule, bool]:
        if task_ids:
            tasks_to_schedule = []
            for task_id in task_ids:
                task = db.get_task(task_id)
                if task and not task.completed:
                    tasks_to_schedule.append(task)
        else:
            tasks_to_schedule = db.get_tasks_for_date(target_date)

        if not tasks_to_schedule:
            return (
                DaySchedule(
                    id=None,
                    date=target_date,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    schedule_items=[],
                    suggestions=["No tasks are scheduled for this day yet."],
                    total_hours=0,
                    efficiency_score=10,
                    task_version="",
                ),
                False,
            )

        current_task_version = AgentPlanner.generate_task_version(tasks_to_schedule)
        date_str = target_date.isoformat()
        if not force_regenerate:
            existing_schedule = db.get_day_schedule(date_str)
            if existing_schedule and existing_schedule.task_version == current_task_version:
                return existing_schedule, False

        generated = AgentPlanner._generate_day_schedule(
            tasks_to_schedule,
            target_date,
            planning_context=planning_context,
        )
        schedule = DaySchedule(
            id=None,
            date=target_date,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            schedule_items=generated["schedule_items"],
            suggestions=generated["suggestions"],
            total_hours=generated["total_hours"],
            efficiency_score=generated["efficiency_score"],
            task_version=current_task_version,
        )
        return schedule, True

    @staticmethod
    def generate_task_version(tasks: List[Task]) -> str:
        import hashlib

        task_info = []
        for task in sorted(tasks, key=lambda current_task: current_task.id):
            task_info.append(
                f"{task.id}:{task.name}:{task.completed}:{task.priority}:{task.due_date}:{task.estimated_hours}"
            )
        return hashlib.md5("|".join(task_info).encode()).hexdigest()

    @staticmethod
    def _generate_day_schedule(tasks: List[Task], target_date: date, *, planning_context: str) -> dict:
        tasks_payload = [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description or "",
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "estimated_hours": task.estimated_hours or 2.0,
                "is_overdue": bool(task.due_date and task.due_date < datetime.now()),
            }
            for task in tasks
        ]

        llm_result = LLMService.generate_structured_output(
            system_prompt=AgentPlanner._build_day_schedule_system_prompt(
                str(target_date),
                [task["id"] for task in tasks_payload],
                planning_context=planning_context,
            ),
            user_prompt=f"Tasks to schedule:\n{tasks_payload}",
            response_model=DayScheduleGenerationResult,
            temperature=0.6,
            max_tokens=900,
        )

        schedule_items = []
        total_hours = 0.0
        for item in llm_result.schedule:
            task = db.get_task(item.task_id)
            if not task:
                continue

            start_hour, start_min = map(int, item.start_time.split(":"))
            end_hour, end_min = map(int, item.end_time.split(":"))
            duration = (end_hour * 60 + end_min - start_hour * 60 - start_min) / 60
            total_hours += duration
            schedule_items.append(
                TaskScheduleItem(
                    task_id=item.task_id,
                    task_name=task.name,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    duration=duration,
                    priority=task.priority,
                    reason=item.reason or "Scheduled based on priority and available time.",
                )
            )

        return {
            "schedule_items": schedule_items,
            "suggestions": llm_result.suggestions,
            "total_hours": total_hours,
            "efficiency_score": llm_result.efficiency_score,
        }

    @staticmethod
    def _build_text_planner_prompt(*, max_tasks: int, now: datetime, planning_context: str) -> str:
        return f"""
You are an AI agent planner for a task management product.
Current time: {now.isoformat(timespec="minutes")}

Use this user context when planning:
{planning_context}

Return exactly one JSON object with this schema:
{{
  "goal_summary": "one-sentence summary of the user goal",
  "project_theme": "short project theme",
  "success_criteria": ["short completion criteria"],
  "plan_rationale": "why this plan structure makes sense",
  "risk_notes": ["execution or planning risks"],
  "tasks": [
    {{
      "name": "concrete action",
      "description": "clear execution details",
      "priority": "low|medium|high",
      "estimated_hours": 2.0,
      "due_date": "optional ISO datetime or null"
    }}
  ]
}}

Requirements:
- Return between 1 and {max_tasks} tasks.
- Make tasks specific and executable.
- Use realistic effort estimates between 0.5 and 6 hours.
- Keep goal_summary and project_theme concise.
- Do not include markdown fences.
""".strip()

    @staticmethod
    def _build_text_loop_prompt(
        *,
        now: datetime,
        planning_context: str,
        available_tools: List[Dict[str, Any]],
        execution_history: List[Dict[str, Any]],
        max_tasks: int,
    ) -> str:
        return f"""
You are an AI agent that plans one next action at a time for a task management product.
Current time: {now.isoformat(timespec="minutes")}

Use this user context when planning:
{planning_context}

Available tools:
{json.dumps(available_tools, ensure_ascii=False, indent=2)}

Previous execution history:
{json.dumps(execution_history, ensure_ascii=False, indent=2)}

Return exactly one JSON object with this schema:
{{
  "goal_summary": "one-sentence summary of the user goal",
  "project_theme": "short project theme",
  "success_criteria": ["short completion criteria"],
  "plan_rationale": "why this next action makes sense",
  "risk_notes": ["execution or planning risks"],
  "is_complete": false,
  "completion_message": "optional completion note or null",
  "planned_task": {{
    "name": "concrete action",
    "description": "clear execution details",
    "priority": "low|medium|high",
    "estimated_hours": 2.0,
    "due_date": "optional ISO datetime or null"
  }},
  "tool_call": {{
    "tool_name": "tool from available tools",
    "arguments": {{}}
  }}
}}

Rules:
- Decide only the next best action, not the full project.
- If the goal has already been sufficiently advanced based on execution history, set "is_complete" to true.
- If "is_complete" is true, both "planned_task" and "tool_call" must be null.
- If "is_complete" is false, return exactly one planned_task and one tool_call.
- Prefer create_task when the user goal should become a tracked task.
- Never invent tools outside the available tools list.
- Keep the total number of created tasks bounded; the system will stop around {max_tasks} iterations.
- Do not include markdown fences.
""".strip()

    @staticmethod
    def _build_image_task_system_prompt(*, max_tasks: int, planning_context: str) -> str:
        return f"""
You are an AI multimodal productivity assistant.
Analyze the image and extract actionable tasks from visible text, layout, and context clues.

Use this user preference and memory context when deciding task priority and estimates:
{planning_context}

Return exactly one JSON object with this schema:
{{
  "scene_summary": "short summary of the image",
  "detected_context": "short project or meeting theme",
  "tasks": [
    {{
      "name": "task title",
      "description": "clear execution details",
      "priority": "low|medium|high",
      "estimated_hours": 1.5,
      "due_date": "optional ISO datetime or null",
      "confidence": 0.85,
      "source_snippet": "supporting text or visual clue"
    }}
  ],
  "warnings": ["ambiguity or quality warning"]
}}

Requirements:
- Return between 0 and {max_tasks} tasks.
- Only return tasks supported by the image.
- Confidence must be between 0 and 1.
- Do not include markdown fences.
""".strip()

    @staticmethod
    def _build_image_task_user_prompt(*, filename: str, notes: str) -> str:
        if notes.strip():
            return (
                f"Image filename: {filename}\n"
                f"Additional user notes:\n{notes.strip()}\n"
                "Extract actionable tasks from the image and notes."
            )
        return f"Image filename: {filename}\nExtract actionable tasks from the image."

    @staticmethod
    def _build_day_schedule_system_prompt(
        target_date: str,
        task_ids: List[str],
        *,
        planning_context: str,
    ) -> str:
        return f"""
You are an AI scheduling assistant.
Schedule tasks for {target_date}.

Use this user context when choosing order, timing, and suggestions:
{planning_context}

Return exactly one JSON object with this schema:
{{
  "schedule": [
    {{
      "task_id": "task id",
      "start_time": "09:00",
      "end_time": "10:30",
      "reason": "why it is scheduled here"
    }}
  ],
  "suggestions": ["short suggestion"],
  "efficiency_score": 8
}}

Guidelines:
- Prioritize overdue and high-priority tasks.
- Avoid impossible overlaps.
- Use work hours between 09:00 and 22:00.
- Keep reasons short and concrete.
- Only use task ids from this list: {task_ids}
- Do not include markdown fences.
""".strip()
