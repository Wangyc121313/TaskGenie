import asyncio
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db.database import db
from app.main import app
from app.models.schemas import AgentExecutionStatus, AIJob, AIJobStatus, PlannedTask, TaskPlanningResult
from app.services.ai_service import AIService
from app.services.task_planning_workflow import TaskPlanningWorkflow


client = TestClient(app)


class TestTaskGenieAPI:
    def setup_method(self):
        db.clear_all()

    def _create_task(self, **overrides):
        payload = {
            "name": "测试任务",
            "description": "这是一个测试任务",
            "priority": "high",
            "estimated_hours": 2.5,
        }
        payload.update(overrides)
        response = client.post("/tasks", json=payload)
        assert response.status_code == 200
        return response.json()

    def _start_ai_task_planning(self, prompt="学习Python编程", max_tasks=3):
        response = client.post(
            "/ai/plan-tasks/async",
            json={"prompt": prompt, "max_tasks": max_tasks},
        )
        assert response.status_code == 200
        return response.json()

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "TaskGenie API v2.0"
        assert "features" in data

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    def test_create_task(self):
        data = self._create_task()
        assert data["name"] == "测试任务"
        assert data["description"] == "这是一个测试任务"
        assert data["priority"] == "high"
        assert data["estimated_hours"] == 2.5
        assert "id" in data
        assert "created_at" in data

    def test_get_all_tasks(self):
        first_task = self._create_task()
        second_task = self._create_task(
            name="第二个任务",
            description="另一个测试任务",
            priority="medium",
            estimated_hours=None,
        )

        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2
        task_ids = [task["id"] for task in data]
        assert first_task["id"] in task_ids
        assert second_task["id"] in task_ids

    def test_get_single_task(self):
        created_task = self._create_task()
        response = client.get(f"/tasks/{created_task['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_task["id"]
        assert data["name"] == created_task["name"]

    def test_get_nonexistent_task(self):
        response = client.get("/tasks/nonexistent-id")
        assert response.status_code == 404
        assert "任务不存在" in response.json()["detail"]

    def test_update_task(self):
        created_task = self._create_task()
        response = client.put(
            f"/tasks/{created_task['id']}",
            json={"name": "更新后的任务名称", "completed": True, "priority": "low"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的任务名称"
        assert data["completed"] is True
        assert data["priority"] == "low"

    def test_delete_task(self):
        created_task = self._create_task()
        response = client.delete(f"/tasks/{created_task['id']}")
        assert response.status_code == 200
        assert "任务已删除" in response.json()["message"]

        get_response = client.get(f"/tasks/{created_task['id']}")
        assert get_response.status_code == 404

    def test_get_available_tags(self):
        response = client.get("/tags")
        assert response.status_code == 200

        data = response.json()
        expected_tags = ["今日", "明日", "重要", "已完成", "已过期"]
        assert "system_tags" in data
        assert "tag_descriptions" in data
        for tag in expected_tags:
            assert tag in data["system_tags"]
            assert tag in data["tag_descriptions"]

    def test_filter_tasks_by_tags(self):
        self._create_task(name="高优先级任务A", priority="high")
        self._create_task(name="中优先级任务", priority="medium")
        self._create_task(name="高优先级任务B", priority="high")

        important_response = client.get("/tasks/by-tags?tags=重要")
        assert important_response.status_code == 200
        assert len(important_response.json()) >= 2

        today_response = client.get("/tasks/by-tags?tags=今天")
        assert today_response.status_code == 200
        assert len(today_response.json()) >= 1

    def test_get_calendar_tasks(self):
        tomorrow = datetime.now() + timedelta(days=1)
        self._create_task(
            name="明天的任务",
            priority="medium",
            due_date=tomorrow.isoformat(),
            estimated_hours=None,
        )

        response = client.get(f"/tasks/calendar/{tomorrow.year}/{tomorrow.month}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        tomorrow_key = tomorrow.date().isoformat()
        if tomorrow_key in data:
            assert "due" in data[tomorrow_key]
            assert isinstance(data[tomorrow_key]["due"], list)

    def test_get_stats(self):
        self._create_task(name="高优先级任务", priority="high")
        self._create_task(name="中优先级任务", priority="medium")
        self._create_task(name="已完成任务", priority="low", completed=True)

        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert data["completed"] >= 1
        assert data["pending"] >= 2
        assert isinstance(data["by_priority"], dict)
        assert isinstance(data["by_status"], dict)
        assert isinstance(data["by_tags"], dict)

    def test_ai_task_planning(self):
        data = self._start_ai_task_planning(prompt="学习Python编程", max_tasks=3)
        assert "job_id" in data
        assert data["status"] == "processing"
        assert data["max_tasks"] == 3

        status_response = client.get(f"/ai/jobs/{data['job_id']}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == data["job_id"]
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]

    def test_ai_job_status(self):
        start_data = self._start_ai_task_planning()
        response = client.get(f"/ai/jobs/{start_data['job_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == start_data["job_id"]
        assert "status" in data
        assert "created_at" in data

    def test_ai_job_not_found(self):
        response = client.get("/ai/jobs/nonexistent-job-id")
        assert response.status_code == 404
        assert "任务不存在" in response.json()["detail"]

    def test_ai_test_endpoint(self):
        response = client.post("/ai/plan-tasks/test?prompt=测试任务&max_tasks=2")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if data["success"]:
            assert "tasks_created" in data
            assert "tasks" in data

    def test_day_schedule_preview(self):
        today = datetime.now().date()
        self._create_task(
            name="今天的任务",
            due_date=datetime.combine(today, datetime.min.time()).isoformat(),
            priority="high",
            estimated_hours=2.0,
        )

        response = client.get(f"/ai/schedule-day/{today.isoformat()}")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == today.isoformat()
        assert "task_count" in data
        assert "total_estimated_hours" in data
        assert "high_priority_count" in data
        assert "tasks" in data
        assert data["task_count"] >= 1
        assert data["high_priority_count"] >= 1

    def test_invalid_task_creation(self):
        response = client.post("/tasks", json={"description": "缺少name字段"})
        assert response.status_code == 422

    def test_invalid_date_format(self):
        response = client.get("/ai/schedule-day/invalid-date")
        assert response.status_code == 400
        assert "日期格式错误" in response.json()["detail"]

    def test_complete_workflow(self):
        created_task = self._create_task(
            name="完整流程测试任务",
            description="测试完整的工作流",
            priority="high",
            estimated_hours=3.0,
        )

        get_response = client.get(f"/tasks/{created_task['id']}")
        assert get_response.status_code == 200

        update_response = client.put(
            f"/tasks/{created_task['id']}",
            json={"completed": True},
        )
        assert update_response.status_code == 200
        assert update_response.json()["completed"] is True

        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        assert stats_response.json()["completed"] >= 1

        delete_response = client.delete(f"/tasks/{created_task['id']}")
        assert delete_response.status_code == 200

    def test_profile_preferences_update(self):
        get_response = client.get("/profile/preferences")
        assert get_response.status_code == 200
        assert get_response.json()["planning_style"] == "balanced"

        update_response = client.put(
            "/profile/preferences",
            json={
                "display_name": "Yuchen",
                "planning_style": "structured",
                "peak_focus_period": "evening",
                "avoid_time_ranges": ["13:00-14:00"],
                "preferred_task_duration_hours": 1.5,
            },
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["display_name"] == "Yuchen"
        assert data["planning_style"] == "structured"
        assert data["peak_focus_period"] == "evening"
        assert data["avoid_time_ranges"] == ["13:00-14:00"]
        assert data["preferred_task_duration_hours"] == 1.5

    def test_profile_memory_crud_and_context_preview(self):
        create_response = client.post(
            "/profile/memories",
            json={
                "category": "constraint",
                "content": "Avoid meetings before 10am when planning tasks.",
                "tags": ["schedule", "morning"],
            },
        )
        assert create_response.status_code == 200
        memory = create_response.json()
        assert memory["category"] == "constraint"
        assert "id" in memory

        list_response = client.get("/profile/memories")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        context_response = client.get(
            "/profile/planning-context",
            params={"prompt": "Plan my morning schedule and focus work"},
        )
        assert context_response.status_code == 200
        context_data = context_response.json()
        assert "preferences" in context_data
        assert len(context_data["relevant_memories"]) == 1
        assert "Avoid meetings before 10am" in context_data["prompt_context"]

        delete_response = client.delete(f"/profile/memories/{memory['id']}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Memory deleted."

    def test_task_auto_extracts_memory_and_updates_preferences(self):
        response = client.post(
            "/tasks",
            json={
                "name": "Focus on AI agent projects this quarter",
                "description": "Avoid meetings before 10am. I prefer 1-hour focus blocks.",
                "priority": "high",
                "estimated_hours": 1.0,
            },
        )
        assert response.status_code == 200

        memories_response = client.get("/profile/memories")
        assert memories_response.status_code == 200
        memories = memories_response.json()
        memory_categories = {memory["category"] for memory in memories}
        memory_texts = [memory["content"] for memory in memories]

        assert "goal" in memory_categories
        assert "constraint" in memory_categories
        assert "preference" in memory_categories
        assert any("Focus on AI agent projects" in content for content in memory_texts)
        assert any("Avoid meetings before 10am" in content for content in memory_texts)
        assert any("prefer 1-hour focus blocks" in content.lower() for content in memory_texts)

        preferences_response = client.get("/profile/preferences")
        assert preferences_response.status_code == 200
        preferences = preferences_response.json()
        assert preferences["preferred_task_duration_hours"] == 1.7

    def test_ai_job_trace_records_planning_and_execution(self, monkeypatch):
        captured = {}

        client.put(
            "/profile/preferences",
            json={
                "planning_style": "structured",
                "priority_preference": "deadline_first",
                "peak_focus_period": "morning",
            },
        )
        client.post(
            "/profile/memories",
            json={
                "category": "goal",
                "content": "Focus on AI agent projects when planning technical work.",
                "tags": ["ai", "career"],
            },
        )
        self._create_task(
            name="Existing high priority work",
            priority="high",
            estimated_hours=4.0,
        )

        def mock_plan_tasks(
            prompt: str,
            max_tasks: int,
            task_type: str,
            now: datetime,
            planning_context: str = "",
        ):
            captured["planning_context"] = planning_context
            return TaskPlanningResult(
                project_theme="Agent Upgrade",
                tasks=[
                    PlannedTask(
                        name="Design workflow trace",
                        description="Persist planner and executor activity for every AI run.",
                        priority="high",
                        estimated_hours=2.0,
                    ),
                    PlannedTask(
                        name="Expose trace in API",
                        description="Return planned tasks, tool calls, and execution status in job responses.",
                        priority="medium",
                        estimated_hours=1.5,
                    ),
                ],
            )

        monkeypatch.setattr(TaskPlanningWorkflow, "plan_tasks", mock_plan_tasks)

        job_id = "trace-job"
        db.create_ai_job(
            AIJob(
                job_id=job_id,
                status=AIJobStatus.PENDING,
                created_at=datetime.now(),
            )
        )

        asyncio.run(
            AIService.process_task_planning(
                job_id=job_id,
                prompt="Develop an AI agent workflow for TaskGenie",
                max_tasks=2,
            )
        )

        job = db.get_ai_job(job_id)
        assert job is not None
        assert job.status == AIJobStatus.COMPLETED
        assert job.trace is not None
        assert job.trace.execution_status == AgentExecutionStatus.COMPLETED
        assert job.trace.current_step == "completed"
        assert job.trace.task_type == "development"
        assert job.trace.project_theme == "Agent Upgrade"
        assert job.trace.preference_snapshot is not None
        assert job.trace.preference_snapshot.planning_style == "structured"
        assert len(job.trace.relevant_memories) == 1
        assert "AI agent projects" in job.trace.relevant_memories[0].content
        assert "structured" in captured["planning_context"]
        assert "AI agent projects" in captured["planning_context"]
        assert "High-priority open tasks: 1." in captured["planning_context"]
        assert len(job.trace.events) >= 6
        assert job.trace.events[0].event_type == "memory_loaded"
        assert job.trace.events[1].event_type == "planning_started"
        assert job.trace.events[2].event_type == "planning_completed"
        assert job.trace.events[3].event_type == "execution_started"
        assert job.trace.events[-1].event_type == "run_completed"
        assert job.trace.events[-1].metadata["created_task_count"] == 2
        assert len(job.trace.planned_tasks) == 2
        assert len(job.trace.tool_calls) == 2
        assert len(job.trace.created_tasks) == 2
        assert all(tool_call.status == "completed" for tool_call in job.trace.tool_calls)
        assert all(tool_call.output is not None for tool_call in job.trace.tool_calls)
        completed_tool_events = [
            event for event in job.trace.events if event.event_type == "tool_completed"
        ]
        assert len(completed_tool_events) == 2
        assert isinstance(job.result, list)
        assert len(job.result) == 2
