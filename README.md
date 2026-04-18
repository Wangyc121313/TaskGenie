# TaskGenie

TaskGenie 是一个任务规划应用，采用 `React Native + FastAPI` 的 monorepo 结构。  
项目围绕三类典型场景展开：

- 将自然语言目标拆解为可执行任务
- 将图片或截图提取为任务候选
- 基于现有任务生成日程安排

后端提供统一的 AI 运行时、工具调用、确认门控、执行轨迹和用户偏好/记忆管理；前端提供任务视图、日历视图、统一 Assistant 入口和 Profile/Memory 管理界面。

## 功能特性

- 任务创建、编辑、删除、完成状态管理
- 日历视图与按日期聚合任务
- 文本目标转任务
- 图片转任务
- 日程规划与保存
- Agent 执行轨迹与决策时间线
- 用户偏好与长期记忆管理
- 高影响写操作的确认执行
- 本地评测 runner 与 CI

## 技术栈

### Mobile

- React Native 0.79
- React 19
- Context API
- Hooks
- Fetch API

### API

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenAI-compatible API client

### Runtime

- Plan-and-Execute
- 轻量迭代 loop
- Tool Registry
- Confirmation Gate
- Structured Trace
- Preferences / Memory Context

### Engineering

- Pytest
- Jest
- ESLint
- GitHub Actions

## 仓库结构

```text
TaskGenie/
├─ apps/
│  ├─ mobile/   # React Native 客户端
│  └─ api/      # FastAPI 后端与 AI Runtime
├─ docs/
│  ├─ agent-architecture.md
│  ├─ demo-walkthrough.md
│  └─ plans/
└─ README.md
```

## 后端架构概览

后端围绕统一的 Agent Runtime 组织，核心模块包括：

- `planner`
  负责生成结构化计划或下一步动作

- `executor`
  负责执行工具调用并记录结果

- `policy`
  负责确认门控和执行策略

- `trace_formatter`
  负责整理前端可消费的响应和轨迹摘要

- `tool_registry`
  统一维护工具元信息、输入输出 schema 和副作用级别

- `memory_service`
  负责用户偏好、长期记忆和规划上下文构建

## 环境变量

API 服务通过 `apps/api/.env` 读取配置，可从 [apps/api/.env.example](C:/Users/22122/Documents/Playground/TaskGenie/apps/api/.env.example) 复制一份后修改。

常用变量如下（以kimi k2.5 模型为例）：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2.5
OPENAI_VISION_MODEL=kimi-k2.5
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

如果使用其他 OpenAI 兼容平台，只需替换：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `OPENAI_VISION_MODEL`

## 本地运行

### 1. 启动 API

```bash
cd apps/api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

或使用：

```bash
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

默认地址：

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. 启动移动端

```bash
cd apps/mobile
npm install
npm start
```

然后在新终端执行：

```bash
cd apps/mobile
npm run android
```

如果使用 Android 模拟器，后端地址默认走 `10.0.2.2:8000`。

## 测试与评测

### API 测试

```bash
cd apps/api
python -m pytest tests -q
```

### Mobile 测试

```bash
cd apps/mobile
npm test -- --watch=false
```

### Mobile lint

```bash
cd apps/mobile
npm run lint:ci
```

### 离线评测

```bash
cd apps/api
python evals/run_evals.py --mode offline --output evals/results/latest.json
```

评测结果会输出到：

[latest.json](C:/Users/22122/Documents/Playground/TaskGenie/apps/api/evals/results/latest.json)

当前离线评测覆盖：

- `text_planning`
- `image_task`
- `memory_hit`

## API 入口

主要接口包括：

- `POST /ai/agent/run`
- `GET /ai/agent/runs/{job_id}`
- `POST /ai/agent/runs/{job_id}/confirm`
- `GET /ai/agent/tools`
- `POST /ai/plan-tasks/async`
- `POST /ai/plan-image/async`
- `POST /ai/schedule-day/async`
- `GET /tasks`
- `GET /stats`
- `GET /profile/preferences`
- `GET /profile/memories`

## 文档

更多说明见：

- [Agent 架构说明](C:/Users/22122/Documents/Playground/TaskGenie/docs/agent-architecture.md)
- [Demo 演示路径](C:/Users/22122/Documents/Playground/TaskGenie/docs/demo-walkthrough.md)
- [Roadmap](C:/Users/22122/Documents/Playground/TaskGenie/docs/plans/2026-04-17-taskgenie-agent-fullstack-roadmap.md)
