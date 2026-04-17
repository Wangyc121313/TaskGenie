# TaskGenie API

FastAPI backend for TaskGenie.

This service now exposes both the original task CRUD API and a unified
agent-oriented runtime for text goals, image-to-task extraction, and day
scheduling.

## Responsibilities

- task CRUD
- task statistics and calendar data
- AI task planning
- AI day scheduling
- unified agent runtime
- user preferences and memory management
- agent trace and execution logs
- persistence for tasks, jobs, and schedules

## Stack

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenAI-compatible API client

## Environment

Create a local `.env` from `.env.example` before starting the API.

Important variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `OPENAI_VISION_MODEL`
- `DATABASE_URL`

The repo keeps only `.env.example`; your real `.env` stays local.

## Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Alternative:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Important Files

- `app/main.py`: FastAPI application entrypoint
- `app/routers/`: HTTP route modules
- `app/services/`: business logic and AI orchestration
- `app/agent/`: planner, executor, policy, and trace runtime
- `app/db/database.py`: persistence layer
- `app/models/schemas.py`: Pydantic schemas and enums
- `app/core/config.py`: environment-driven settings
- `app/core/logging_utils.py`: structured agent logging helpers
- `tests/test_api.py`: API regression test suite
- `evals/`: lightweight regression datasets for planning, image extraction, and memory
