# TaskGenie 系统架构文档

> 本文档梳理 TaskGenie 的整体分层结构、API 接口定义、核心数据模型、数据流向与前端模块组织，供功能迭代前的架构参考使用。

---

## 一、整体分层结构

```
┌─────────────────────────────────────┐
│         Mobile (React Native)        │
│  App.tsx → Hooks → Components/Tabs  │
└──────────────┬──────────────────────┘
               │ HTTP / JSON (Fetch API)
┌──────────────▼──────────────────────┐
│         FastAPI Backend              │
│  Routers → Services → Agent Runtime │
│  DB Layer (SQLAlchemy/SQLite/PG)     │
└──────────────┬──────────────────────┘
               │ OpenAI-compatible API
┌──────────────▼──────────────────────┐
│         LLM Provider                 │
└─────────────────────────────────────┘
```

---

## 二、API 接口全量清单

### `/tasks` — 任务 CRUD

| 方法 | 路径 | 描述 | 请求体 | 返回 |
|------|------|------|--------|------|
| `POST` | `/tasks` | 创建任务 | `TaskCreate` | `Task` |
| `GET` | `/tasks` | 获取所有任务 | — | `Task[]` |
| `GET` | `/tasks/{task_id}` | 获取单个任务 | — | `Task` |
| `PUT` | `/tasks/{task_id}` | 更新任务 | `TaskUpdate` | `Task` |
| `DELETE` | `/tasks/{task_id}` | 删除任务 | — | `{message}` |
| `GET` | `/tasks/by-tag/{tag}` | 按单标签过滤 | — | `Task[]` |
| `GET` | `/tasks/by-tags?tags=a,b` | 按多标签过滤 | — | `Task[]` |
| `GET` | `/tasks/calendar/{year}/{month}` | 按月聚合任务 | — | 按日期分组的任务 |

---

### `/ai` — Agent 与 AI 功能

| 方法 | 路径 | 描述 | 请求体 | 返回 |
|------|------|------|--------|------|
| `POST` | `/ai/agent/run` | 启动 Agent Run（三种 mode） | `AgentRunRequest` | `AgentRunResponse` |
| `GET` | `/ai/agent/runs/{job_id}` | 查询 Agent Run 状态 | — | `AgentRunResponse` |
| `POST` | `/ai/agent/runs/{job_id}/confirm` | 确认高影响操作后继续执行 | — | `AgentRunResponse` |
| `GET` | `/ai/agent/tools` | 列出所有注册工具 | — | `ToolDefinitionSchema[]` |
| `GET` | `/ai/conversations/{conversation_id}` | 获取会话历史 | — | `ConversationSession` |
| `POST` | `/ai/transcribe` | 音频 Base64 → 文字（Whisper） | `AITranscribeRequest` | `AITranscribeResponse` |

`AgentRunRequest` 的 `mode` 字段决定 Runtime 走哪条执行分支：

| mode | 触发场景 | 核心产出 |
|------|----------|----------|
| `text_goal` | 用户输入自然语言目标 | `PlannedTask[]` → 写入 DB |
| `image_goal` | 用户上传图片/截图 | `ImageTaskCandidate[]` → 用户确认后写入 DB |
| `schedule_day` | 用户请求某天日程安排 | `DaySchedule` → 持久化到 DB + 前端展示 |

---

### `/mcp` — MCP 工具协议

| 方法 | 路径 | 描述 | 请求体 | 返回 |
|------|------|------|--------|------|
| `GET` | `/mcp/tools/list` | 列出 MCP 格式工具描述 | — | `MCPToolsListResponse` |
| `POST` | `/mcp/tools/call` | 调用指定工具 | `MCPToolCallRequest` | `MCPToolCallResponse` |

---

### `/profile` — 用户偏好与记忆

| 方法 | 路径 | 描述 | 请求体 | 返回 |
|------|------|------|--------|------|
| `GET` | `/profile/preferences` | 获取用户偏好 | — | `UserPreferences` |
| `PUT` | `/profile/preferences` | 更新用户偏好 | `UserPreferencesUpdate` | `UserPreferences` |
| `GET` | `/profile/memories` | 列出记忆（可按 category 过滤） | — | `UserMemoryItem[]` |
| `POST` | `/profile/memories` | 创建记忆条目 | `UserMemoryCreate` | `UserMemoryItem` |
| `PUT` | `/profile/memories/{id}` | 更新记忆 | `UserMemoryUpdate` | `UserMemoryItem` |
| `DELETE` | `/profile/memories/{id}` | 删除记忆 | — | `{message}` |
| `GET` | `/profile/planning-context?prompt=` | 预览 Agent 规划前加载的上下文 | — | `UserPlanningContext` |

---

### `/stats` `/tags` — 通用

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/stats` | 任务统计汇总 |
| `GET` | `/tags` | 获取所有可用标签 |

---

## 三、核心数据模型

```
Task
├── id, name, description
├── completed, status (pending / in_progress / completed)
├── priority (low / medium / high)
├── due_date, scheduled_date, estimated_hours
└── created_at

UserPreferences  (1对1, user_id)
├── work_start_time, work_end_time
├── peak_focus_period (morning / afternoon / evening / split)
├── planning_style (structured / balanced / flexible)
├── priority_preference (deadline_first / impact_first / balanced)
├── max_daily_focus_hours, preferred_task_duration_hours
├── break_interval_minutes
└── avoid_time_ranges[]

UserMemoryItem  (1对多, user_id)
├── category (preference / constraint / goal / habit / context)
├── source (user_confirmed / system_inferred / user_edited)
├── content, tags[], source_confidence
└── is_active, relevance_score, last_used_at

AIJob
├── job_id, status (pending / processing / awaiting_confirmation / completed / failed)
├── created_at
└── → AgentRunResponse
         ├── status, summary
         ├── artifacts.created_tasks[]
         └── trace.decision_timeline[]
```

---

## 四、数据流向图

### 4.1 文本目标 → 任务创建

```
用户输入 goal 文本
       │
       ▼
[AIPlanningModal / AssistantTab]
       │  POST /ai/agent/run { mode: "text_goal", goal }
       ▼
[AgentRuntime.run()]
       │
       ├─ 1. MemoryService.build_planning_context()
       │        └─ 加载 UserPreferences + 相关 UserMemoryItem
       │
       ├─ 2. AgentPlanner.plan_text_goal()
       │        └─ 调用 LLM → AgentTaskPlanResult
       │             (goal_summary, tasks[], success_criteria)
       │
       ├─ 3. build_task_creation_tool_calls()
       │        └─ 每个 PlannedTask → AgentToolCallTrace
       │             (tool: create_task, side_effect: WRITE)
       │
       ├─ 4. policy.should_require_confirmation()
       │        ├─ auto_execute=true  → 直接执行
       │        └─ auto_execute=false → 返回 AWAITING_CONFIRMATION
       │                    │
       │           用户点击确认
       │           POST /ai/agent/runs/{id}/confirm
       │                    │
       ├─ 5. executor.execute_tool_calls()
       │        └─ ToolRegistry → TaskService.create_task() → 写入 DB
       │
       └─ 6. trace_formatter → AgentRunResponse
                └─ 前端 useAgentAssistant 收到 artifacts.created_tasks[]
                       → fetchTasks() 刷新列表
```

### 4.2 图片 → 任务候选

```
用户选取图片
       │
       ▼
[AIImagePlanningModal]
       │  POST /ai/agent/run { mode: "image_goal", image_base64 }
       ▼
[AgentRuntime._run_image_goal()]
       │
       ├─ Stage 1: AgentPlanner.transcribe_image_to_text()
       │     └─ 视觉模型仅做内容提取（文字原样转录 / 图表结构描述）
       │
       ├─ Stage 2: AgentPlanner.extract_tasks_from_transcription()
       │     └─ 文本 LLM 根据转录内容规划任务 → ImageTaskExtractionResult
       │          (scene_summary, tasks: ImageTaskCandidate[])
       │
       └─ 返回候选列表（此阶段不写 DB）
              │
       用户在前端勾选候选项并确认
              │
       [createTasksFromCandidates()]
              │  循环 POST /tasks
              └─ 写入 DB → fetchTasks()
```

### 4.3 日程生成

```
用户选择日期 + 任务列表
       │
       ▼
[AIScheduleModal]
       │  POST /ai/agent/run { mode: "schedule_day", date, task_ids[] }
       ▼
[AgentRuntime._run_day_schedule()]
       │
       ├─ 读取 task_ids 对应的 Task[]
       ├─ MemoryService 加载用户偏好（work_start/end_time 等）
       ├─ AgentPlanner.plan_day_schedule()
       │     └─ 调用 LLM → DayScheduleGenerationResult
       │          (schedule: [{ task_id, start_time, end_time, reason }],
       │           efficiency_score, suggestions[])
       │
       └─ 返回 schedule 供前端展示
          schedule 在生成时由 Runtime 自动写入 DB（db.create_day_schedule）
          再次打开同一日期的 Modal 时直接加载已保存结果
```

---

## 五、前端模块结构

```
App.tsx
├── TaskProvider  (Context: selectedTags, modal 状态)
│
├── Utils  (src/utils/)
│   ├── config.js            API_URL 配置（单一配置点，Platform 自动选择）
│   └── api.js               apiFetch 统一请求层（URL 注入 + JSON headers）
│
├── Hooks  (业务逻辑层，唯一与 API 通信的位置)
│   ├── useTaskOperations    → /tasks 系列接口
│   ├── useAgentAssistant    → /ai/agent/run, /confirm（文本/图片规划）
│   ├── useAgentJob          → 通用 Agent job 启动 + 轮询（供 Modals 直接使用）
│   ├── useProfileData       → /profile 系列接口
│   ├── useVoiceInput        → @react-native-voice/voice 语音输入封装
│   └── usePullDownSearch    → 搜索过滤（本地）
│
├── Tabs  (页面视图)
│   ├── TaskListTab          ← useTaskOperations
│   ├── CalendarTab          ← useTaskOperations
│   ├── AssistantTab         ← useAgentAssistant
│   └── ProfileTab           ← useProfileData
│
└── Modals  (弹层，触发 AI 流程或手动 CRUD)
    ├── AIPlanningModal      → mode: text_goal（含语音输入）
    ├── AIImagePlanningModal → mode: image_goal（两阶段：视觉转录 + 文本规划）
    ├── AIScheduleModal      → mode: schedule_day（使用 useAgentJob）
    └── TaskModal            → 手动创建/编辑任务
```

---

## 六、Agent Runtime 内部模块职责

```
AgentRuntime  (生命周期协调器)
│
├── AgentPlanner        与 LLM 通信，生成结构化计划产物
│   ├── plan_text_goal()                    → AgentTaskPlanResult
│   ├── transcribe_image_to_text()          → str（视觉模型转录，不做推理）
│   ├── extract_tasks_from_transcription()  → ImageTaskExtractionResult（文本 LLM 规划）
│   ├── extract_image_tasks()               → ImageTaskExtractionResult（直接视觉路径，可选用）
│   └── plan_day_schedule()                 → DayScheduleGenerationResult
│
├── policy              判断是否需要人工确认
│   └── should_require_confirmation(tool_calls, auto_execute)
│
├── executor            将计划转为工具调用并执行
│   ├── build_task_creation_tool_calls()
│   └── execute_tool_calls()  → ToolRegistry
│
├── ToolRegistry        工具注册与分发（MCP 风格）
│   ├── create_task / update_task / delete_task / list_tasks
│   ├── schedule_day / get_stats / search_recent_tasks
│   └── save_user_preference
│   所有工具：输入输出均通过 Pydantic 强类型约束
│             side_effect_level: READ / WRITE / DESTRUCTIVE
│
└── trace_formatter     将执行过程格式化为前端可消费的结构
    └── format_job_as_agent_response() → AgentRunResponse
         ├── status, summary
         ├── artifacts.created_tasks[]
         └── trace.decision_timeline[]
```

Runtime 模块与 LangGraph 节点概念的对应关系（为未来迁移保留路径）：

| 当前模块 | LangGraph 节点概念 |
|----------|--------------------|
| `planner` | planning node |
| `policy` | routing / branching node |
| `executor` | tool execution node |
| `trace_formatter` | summary node |
| Confirmation Gate | human-in-the-loop gate |

---

## 七、当前已知的结构性缺口

> 以下缺口已于 2026-04-27 本次迭代中全部修复。

| 问题 | 位置 | 状态 |
|------|------|------|
| `API_URL` 硬编码在 Context 里 | `src/context/TaskContext.js` | ✅ 已迁移至 `src/utils/config.js`，Platform 自动选择，TaskContext 保留向后兼容导出 |
| 旧版 `/ai/plan-tasks/async` 与新 Agent 并存 | `routers/ai.py` | ✅ 旧版端点已删除；`aiPlanTasks` 改走 `POST /ai/agent/run (text_goal)` |
| 前端无统一 API 层，`fetch` 散落在各 Hook | `src/hooks/` | ✅ 新增 `src/utils/api.js` (`apiFetch`)；全部 Hook 和 AIScheduleModal 已切换 |
| Agent mode 入口分散于多个独立 Modal | `src/components/` | ✅ 新增 `useAgentJob` Hook 统一封装 Agent 启动 + 轮询；AIScheduleModal 已使用 |
| `schedule_day` 结果只展示、不持久化 | `AIScheduleModal.js` | ✅ 后端 Runtime 本已写 DB；前端 `fetchDayPreview` 现在同时调用 `GET /ai/schedule/{date}` 并展示已保存日程 |
| 旧版 async job 缺少 polling 逻辑 | `src/hooks/` | ✅ `aiPlanTasks` 已改走 Agent endpoint，polling 指向 `GET /ai/agent/runs/{job_id}` |
