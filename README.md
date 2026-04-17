# TaskGenie

TaskGenie is an AI-native task planning application built around a mobile client, a formal agent runtime, and an explainable planning API.

The current product focuses on three primary user flows:

- turn a natural-language goal into a list of executable tasks
- turn an image or screenshot into candidate tasks
- generate a day plan from existing tasks

This repository is organized as a monorepo so the mobile app and the API can evolve together in one place.

## What This Project Is

TaskGenie is not just a CRUD todo app. It tries to turn vague user intent into structured execution:

- users enter a goal in natural language
- the backend calls an LLM to break it into tasks
- the mobile app displays, edits, and tracks those tasks
- users can ask the system to schedule a day automatically

The current architecture now exposes a hand-rolled `Plan-and-Execute` runtime:

- planner
- policy / confirmation gate
- executor
- trace formatter
- editable memory + preferences

That makes the repo significantly closer to an AI agent portfolio project than a simple "LLM feature" demo.

## Repository Layout

```text
TaskGenie/
+-- apps/
|   +-- mobile/   # React Native client
|   +-- api/      # FastAPI backend
+-- README.md
```

This layout is intentional:

- keeping client and server separate is normal
- putting both under `apps/` makes the monorepo easier to understand
- the root should explain the product, not duplicate app-specific setup details

## Tech Stack

### Mobile

- React Native 0.79
- React 19
- Context API + hooks
- Fetch API
- Unified Assistant tab
- Profile + Memory management tab

### API

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenAI-compatible SDK
- Hand-rolled agent runtime with confirmation gates
- Structured trace + decision timeline

## Current Capabilities

- task creation, update, deletion, and calendar view
- AI task decomposition from free-form prompts
- AI agent run preview and confirmation flow
- AI day scheduling based on due date and priority
- image-to-task extraction with multimodal input
- user preferences and editable long-term memory
- local persistence for tasks, schedules, and async AI jobs

## Run Locally

### 1. Start the API

```bash
cd apps/api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The API runs on `http://localhost:8000`.

### 2. Start the mobile app

```bash
cd apps/mobile
npm install
npm start
```

In a second terminal:

```bash
cd apps/mobile
npm run android
```

Or:

```bash
cd apps/mobile
npm run ios
```

## API Endpoint Configuration

The mobile app currently reads the backend URL from:

`apps/mobile/src/context/TaskContext.js`

Default values:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://localhost:8000`

## Why This Refactor

This repository originally came from two separate GitHub projects. After merging them, the structure still looked like a temporary migration.

This refactor fixes that:

- the root README now explains the product
- the repository now uses an `apps/` layout instead of exposing raw `frontend/` and `backend/`
- app-specific documentation stays inside each subproject

## Next Direction

The next major upgrades after this iteration are:

- automated eval runners over the local regression datasets
- richer assistant UX polish and demo assets
- deeper schedule confirmation and explanation
- optional migration to a graph framework if the runtime graph grows

## Recent Refactor

The API codebase now uses a package layout instead of flat top-level modules:

- `apps/api/app/main.py`
- `apps/api/app/routers/`
- `apps/api/app/services/`
- `apps/api/app/db/`
- `apps/api/app/models/`
- `apps/api/tests/`

## Architecture Docs

- [Agent Architecture](docs/agent-architecture.md)
- [Demo Walkthrough](docs/demo-walkthrough.md)
- [Roadmap](docs/plans/2026-04-17-taskgenie-agent-fullstack-roadmap.md)
