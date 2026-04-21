from app.agent.planner import AgentPlanner


def test_analyze_task_type_uses_weighted_signals():
    assert AgentPlanner.analyze_task_type("Implement the FastAPI MCP client bridge") == "development"
    assert AgentPlanner.analyze_task_type("Plan my week and schedule focus blocks") == "planning"
    assert AgentPlanner.analyze_task_type("Study agent memory design patterns") == "learning"
    assert AgentPlanner.analyze_task_type("Write the README and polish the docs") == "writing"


def test_analyze_task_type_supports_common_chinese_signals():
    assert AgentPlanner.analyze_task_type("实现多轮对话能力并修复接口问题") == "development"
    assert AgentPlanner.analyze_task_type("安排明天的学习计划和时间块") == "planning"
    assert AgentPlanner.analyze_task_type("学习 LangGraph 和 Agent 设计模式") == "learning"
