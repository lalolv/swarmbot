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
uv run python -m swarmbot.worker.main          # Start worker
uv run uvicorn swarmbot.api.main:app --host 0.0.0.0 --port 8000 --reload  # Start API
uv run python scripts/publish_demo_task.py           # Submit demo task
```

### Frontend
```bash
cd frontend && npm install && npm run dev            # Dev server on :5173 (proxies /api → :8000)
```

### Lint / Format / Test
```bash
uv run python -m compileall swarmbot scripts   # Minimum syntax check
uv run ruff check --fix swarmbot scripts       # Lint + auto-fix
uv run ruff format swarmbot scripts            # Format
uv run pytest                                        # Full test suite
uv run pytest tests/test_file.py::test_name -q       # Single test
uv run pytest -x                                     # Stop on first failure
```

No `tests/` directory exists yet. Always run `compileall` as minimum verification.

## Architecture

Four backend layers under `swarmbot/`:

- **`shared/`** — Redis client wrapper, channel/key naming (`Channels`, `StreamName`, `SignalType`), domain models (`TaskConfig`, `TaskStatus`, `TaskState`), Pydantic schemas
- **`robots/`** — `BaseRobot` ABC; `RustRobotProxy` for Rust subprocess robots; `TaskComposer` auto-discovers and instantiates robots
- **`worker/`** — `TaskManager` listens to control channel, manages task lifecycle; `RobotTask` composes robots, monitors config, handles hot-reload; `ExecutionDedupe` prevents duplicate task startup
- **`api/`** — FastAPI routes under `/api/v1/`. Task CRUD publishes to control channel. SSE bridge at `/api/v1/live/subscribe/{task_id}` converts Redis Streams → Server-Sent Events

Frontend (`frontend/src/`): Vue 3 app with Pinia store (`stores/observability.js`) managing SSE subscription, robot state, and stream counters.

### Task Lifecycle
1. API creates task → publishes to Redis control channel
2. Worker's `TaskManager` picks it up → `RobotTask.run()` starts
3. `TaskComposer.compose()` instantiates robots per `TaskConfig.robots` (`robots` is required, no implicit defaults)
4. Robots emit signals to task-scoped streams (`swarmbot:task:TASK_ID:stream:NAME`)
5. SSE bridge streams events to frontend in real-time
6. PATCH triggers hot-reload (robots stop and restart with new config); DELETE cancels/purges

### Key Contracts
- **Stream names** are defined in `StreamName` enum (`channels.py`); `Channels.ALL_STREAMS` is auto-generated from it — add streams there, not as bare strings
- **Signal payloads** are JSON with `ensure_ascii=False`; keep schema stable across producer/consumer
- **API response envelopes** use consistent fields (`accepted`, `task_id`, `message`)
- **Robot status** is event-driven: `BaseRobot` calls `status_callback` on every `emit()` and `signals_in` increment; a 30s heartbeat in `RobotTask` provides liveness confirmation

## Robot Development

### Adding a Python Robot
Create `swarmbot/robots/my_bot/` with `__init__.py` and `robot.py`. `TaskComposer` auto-discovers all `*_bot/` directories — no manual registration needed.

```python
class MyBot(BaseRobot):
    robot_type = "my_bot"           # Must match directory name exactly
    input_streams = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
    status_broadcast_min_interval = 2.0  # Throttle for high-frequency bots

    async def setup(self) -> None:
        self._loop_task = asyncio.create_task(self._my_loop())

    async def teardown(self) -> None:
        self._loop_task.cancel()
        await asyncio.gather(self._loop_task, return_exceptions=True)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, {...})

    def get_runtime_metrics(self) -> dict[str, Any]:
        return {"custom_counter": self._counter}  # Sent to frontend with status
```

### Adding a Rust Robot
Subclass `RustRobotProxy`. The Rust binary communicates directly with Redis; Python only manages the process lifecycle.

```python
class TradingBot(RustRobotProxy):
    robot_type = "trading_bot"
    rust_binary = "/path/to/target/release/trading-bot"
    input_streams = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
```

The Rust process receives `TASK_ID`, `REDIS_URL`, `INPUT_STREAMS`, `OUTPUT_STREAMS`, and `BOT_*` env vars (simple-typed config fields). It must write `robot_start`/`robot_stop`/`robot_error` signals to the control stream and respond to `SIGTERM` for graceful shutdown.

### Task Robot Spec (`robots`)
When creating a task, specify robots via top-level `robots`:
```json
{
  "robots": [
    {"type": "ticker_bot", "config": {"poll_interval": 3.0}},
    {"type": "transform_bot", "config": {"key": "value"}},
    {"type": "disabled_bot", "enabled": false}
  ]
}
```
`robots` is required and must contain at least one enabled robot.

## Code Conventions

- **Async-first**: no blocking I/O in async paths; use `asyncio.to_thread()` when unavoidable
- **Type hints**: modern style (`str | None`, `list[str]`, `dict[str, Any]`)
- **Imports**: three groups (stdlib / third-party / local), absolute from `swarmbot`
- **Naming**: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Logging**: `loguru.logger` with context (`task_id`, `robot_type`, `stream`, `stage`)
- **Comments**: some files use Chinese — match existing language in each file
- **Architecture boundaries**: keep `api/`, `worker/`, `robots/`, `shared/` separation

## Environment Variables
- `REDIS_URL` — default `redis://localhost:6379/0`
- `EXECUTION_DEDUPE_TTL_SECONDS` — default `300`
