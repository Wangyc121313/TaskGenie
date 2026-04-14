# TaskGenie

TaskGenie is a task planning application built around a mobile client and an AI-assisted API.

The current product focuses on two user flows:

- turn a natural-language goal into a list of executable tasks
- generate a day plan from existing tasks

This repository is organized as a monorepo so the mobile app and the API can evolve together in one place.

## What This Project Is

TaskGenie is not just a CRUD todo app. It tries to turn vague user intent into structured execution:

- users enter a goal in natural language
- the backend calls an LLM to break it into tasks
- the mobile app displays, edits, and tracks those tasks
- users can ask the system to schedule a day automatically

At the moment, the AI layer is still closer to "LLM-powered planning" than a full agent architecture. That makes the repo a good base for future AI-agent refactoring.

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

### API

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenAI-compatible SDK

## Current Capabilities

- task creation, update, deletion, and calendar view
- AI task decomposition from free-form prompts
- AI day scheduling based on due date and priority
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

The current architecture is a solid base for a stronger AI application or AI-agent portfolio project. The next major upgrade would be adding:

- structured LLM outputs instead of manual JSON parsing
- tool-calling workflows
- memory and preference storage
- evaluation and tracing
- agent-style planning and execution loops

## Recent Refactor

The API codebase now uses a package layout instead of flat top-level modules:

- `apps/api/app/main.py`
- `apps/api/app/routers/`
- `apps/api/app/services/`
- `apps/api/app/db/`
- `apps/api/app/models/`
- `apps/api/tests/`
