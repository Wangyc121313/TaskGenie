# TaskGenie

TaskGenie 是一个任务规划应用，采用 `React Native + FastAPI` 的 monorepo 结构。  
项目围绕三类典型场景展开：

- 将自然语言目标拆解为可执行任务
- 语音输入驱动任务规划
- 将图片或截图提取为任务候选
- 基于现有任务生成日程安排

后端提供统一的 AI 运行时、工具调用、确认门控、执行轨迹和用户偏好/记忆管理；前端提供任务视图、日历视图、统一 Assistant 入口和 Profile/Memory 管理界面。

## 功能特性

- 任务创建、编辑、删除、完成状态管理
- 日历视图与按日期聚合任务
- 文本目标转任务
- **语音输入**：麦克风按钮实时识别普通话/英文，自动填充规划输入框
- 图片转任务（两阶段流水线：视觉模型提取内容 → 文本 LLM 规划任务）
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
- `@react-native-voice/voice`（设备端语音识别）

### API

- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL / SQLite
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
  负责生成结构化计划或下一步动作；`transcribe_image_to_text` 以极简 prompt 调用视觉模型做纯内容提取，`extract_tasks_from_transcription` 将提取结果交给文本 LLM 进行任务规划

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

API 服务通过 `apps/api/.env` 读取配置，可从 apps/api/.env.example 复制一份后修改。

常用变量如下（以kimi k2.5 模型为例）：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2.5
OPENAI_VISION_MODEL=kimi-k2.5
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

> `OPENAI_VISION_MODEL` 仅在图片规划的 Stage 1（内容提取）中调用，使用极简 prompt，不做任何任务推理。任务规划逻辑全部由 `OPENAI_MODEL`（文本模型）承担，节省视觉模型推理成本。

如果使用其他 OpenAI 兼容平台，只需替换：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `OPENAI_VISION_MODEL`

数据库连接通过 `DATABASE_URL` 控制，支持 PostgreSQL 和 SQLite；未配置时默认使用本地 SQLite。

## 本地运行

### 1. 启动 API

```bash
cd apps/api
python -m venv venv
```

激活虚拟环境：

```bash
# macOS / Linux
source venv/bin/activate

# Windows Git Bash
source venv/Scripts/activate

# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat
```

```bash
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
```

> 依赖中已包含 `@react-native-voice/voice`，首次在 Android 上运行需完整编译原生模块。

启动 Metro bundler（终端 1）：

```bash
cd apps/mobile
npm start -- --port 8082
```

安装并启动 App（终端 2）：

```bash
cd apps/mobile
# android
npx react-native run-android --port 8082
# ios
npm run ios
```

如果使用 Android 模拟器，后端地址默认走 `10.0.2.2:8000`。

> **首次安装语音模块后需重新编译**：
> ```bash
> cd apps/mobile/android && ./gradlew clean
> cd .. && npx react-native run-android --port 8082
> ```

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

评测结果会输出到：`evals/results/latest.json`

当前离线评测覆盖：

- `text_planning`
- `image_task`
- `memory_hit`

## API 入口

主要接口包括：

| 接口 | 说明 |
|---|---|
| `POST /ai/agent/run` | 启动 Agent 任务 |
| `GET /ai/agent/runs/{job_id}` | 轮询任务状态 |
| `POST /ai/agent/runs/{job_id}/confirm` | 确认高影响操作 |
| `GET /ai/agent/tools` | 查询可用工具列表 |
| `POST /ai/plan-tasks/async` | 文本目标 → 任务拆解 |
| `POST /ai/plan-image/async` | 图片 → 任务提取（两阶段：视觉转录 + 文本规划）|
| `POST /ai/transcribe` | 音频 Base64 → 文字（Whisper） |
| `POST /ai/schedule-day/async` | 任务 → 日程规划 |
| `GET /tasks` | 任务列表 |
| `GET /stats` | 任务统计 |
| `GET /profile/preferences` | 用户偏好 |
| `GET /profile/memories` | 长期记忆 |
| `GET /mcp/tools/list` | MCP 工具列表 |
| `POST /mcp/tools/call` | MCP 工具调用 |

## 文档

更多说明见：

- [Agent 架构说明](docs/agent-architecture.md)
- [Demo 演示路径](docs/demo-walkthrough.md)
- [Roadmap](docs/plans/2026-04-17-taskgenie-agent-fullstack-roadmap.md)
