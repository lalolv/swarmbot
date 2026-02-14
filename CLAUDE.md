# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Redis Streams + Worker + SSE backend scaffold for managing autonomous robot systems that execute tasks asynchronously. Includes a Vue 3 frontend for real-time observability.

**Stack**: Python 3.12 (uv), FastAPI, async Redis, Loguru, Vue 3 + Vite + Tailwind CSS + Pinia

## Commands

### Backend
```bash
uv sync                                              # Install Python deps
cp .env.example .env                                 # First-time env setup
docker run --rm -p 6379:6379 redis:7                 # Start local Redis
uv run python -m pm_sports_bots.worker.main          # Start worker
uv run uvicorn pm_sports_bots.api.main:app --host 0.0.0.0 --port 8000 --reload  # Start API
uv run python scripts/publish_demo_task.py           # Submit demo task
```

### Frontend
```bash
cd frontend && npm install && npm run dev            # Dev server on :5173 (proxies /api → :8000)
```

### Lint / Format / Test
```bash
uv run python -m compileall pm_sports_bots scripts   # Minimum syntax check
uv run ruff check --fix pm_sports_bots scripts       # Lint + auto-fix
uv run ruff format pm_sports_bots scripts            # Format
uv run pytest                                        # Full test suite
uv run pytest tests/test_file.py::test_name -q       # Single test
uv run pytest -x                                     # Stop on first failure
```

No `tests/` directory exists yet. Always run `compileall` as minimum verification.

## Architecture

Four backend layers under `pm_sports_bots/`:

- **`shared/`** — Redis client wrapper, channel/key naming (`Channels`), domain models (`TaskConfig`, `TaskStatus`, `TaskState` enum), Pydantic schemas
- **`robots/`** — `BaseRobot` ABC with two modes: **Producer** (polling via `on_tick()`) and **Consumer** (stream-based `on_signal()`). `TaskComposer` is the factory/registry for robot types
- **`worker/`** — `TaskManager` listens to control channel, manages task lifecycle. `RobotTask` is the runtime container per task (composes robots, monitors config, handles hot-reload)
- **`api/`** — FastAPI routes under `/api/v1/`. Task CRUD publishes to control channel. SSE bridge at `/api/v1/live/subscribe/{task_id}` converts Redis Streams → Server-Sent Events

Frontend (`frontend/src/`): Vue 3 app with Pinia store (`stores/observability.js`) managing SSE subscription, robot state, and stream counters.

### Task Lifecycle
1. API creates task → publishes to Redis control channel
2. Worker's TaskManager picks it up → TaskComposer instantiates robots
3. Robots emit signals to task-scoped streams (`pm_sports_bots:task:TASK_ID:stream:NAME`)
4. SSE bridge streams events to frontend in real-time
5. PATCH triggers hot-reload; DELETE cancels/purges

### Key Contracts
- Redis keys/streams are centralized in `Channels` — update `Channels.ALL_STREAMS` when adding streams
- New robots must extend `BaseRobot` and register via `TaskComposer`
- Signal payloads are JSON with `ensure_ascii=False`; keep schema stable
- API response envelopes use consistent fields (`accepted`, `task_id`, `message`)

## Code Conventions

- **Async-first**: no blocking I/O in async paths; use `asyncio.to_thread()` when unavoidable
- **Type hints**: modern style (`str | None`, `list[str]`, `dict[str, Any]`)
- **Imports**: three groups (stdlib / third-party / local), absolute from `pm_sports_bots`
- **Naming**: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Logging**: `loguru.logger` with context (`task_id`, `robot_type`, `stream`, `stage`)
- **Comments**: some files use Chinese — match existing language in each file
- **Architecture boundaries**: keep `api/`, `worker/`, `robots/`, `shared/` separation

## Environment Variables
- `REDIS_URL` — default `redis://localhost:6379/0`
- `EXECUTION_DEDUPE_TTL_SECONDS` — default `300`
