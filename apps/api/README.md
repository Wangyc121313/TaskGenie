# TaskGenie API

FastAPI backend for TaskGenie.

## Responsibilities

- task CRUD
- task statistics and calendar data
- AI task planning
- AI day scheduling
- persistence for tasks, jobs, and schedules

## Stack

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- OpenAI-compatible API client

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
- `app/db/database.py`: persistence layer
- `app/models/schemas.py`: Pydantic schemas and enums
- `app/core/config.py`: environment-driven settings
- `tests/test_api.py`: API regression test suite
