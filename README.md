<div align="center">

# Swarmbot

**Task-driven swarm orchestration for agentic and prefab robots**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)

*Compose robot swarms. Let signals flow. Watch tasks come alive.*

[中文文档](./README.zh.md)

</div>

---

## Why Swarmbot?

We believe the future is **task-driven** — complex work will be decomposed into tasks, each executed collaboratively by a swarm of specialized robots communicating through signals.

Swarmbot is a runtime for exactly this: you declare a task, compose a team of robots, and the system handles orchestration, communication, and real-time observability.

### Core Design Principles

**1. Tasks are first-class citizens**

Everything starts with a task. A task is not just a job to run — it is a self-contained unit of work with its own robot team, communication channels, and lifecycle. Create it, patch it on the fly, put it to sleep, wake it up, or kill it — the task is the single point of control.

**2. Swarm collaboration over monolithic agents**

Instead of one large agent doing everything, Swarmbot decomposes work across a swarm of focused robots. Each robot does one thing well and communicates with others through signals on Redis Streams. This "hive mind" architecture scales naturally — add more robots to a task without changing existing ones.

**3. Determinism and creativity coexist**

Every real-world task contains both deterministic and creative work. Deterministic code — like `1 + 1 = 2` — ensures the system is **reliable**: data fetching, math transforms, and format conversions always produce the same result. Creative code — powered by AI — ensures the system is **innovative**: each run may generate different insights, content, or strategies.

Swarmbot embraces this duality. The same universal `BaseRobot` interface can host a deterministic polling bot and an LLM-driven analysis bot side by side. You choose the nature of each robot's logic; the framework treats them identically.

**4. Signals as the universal language**

Robots never call each other directly. All communication flows through typed signals on task-scoped Redis Streams. This decoupling means robots can be added, removed, or replaced without touching the rest of the swarm.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Task                                       │
│                                                                         │
│  ┌───────────┐                             ┌───────────┐                │
│  │ ticker_bot│── data stream ────────────►│ analyst_bot│                │
│  │ (polling) │   {value: 42.0}            │ (LLM)     │                │
│  └───────────┘                             └─────┬─────┘                │
│                                                   │                     │
│  ┌────────────┐◄── output stream ────────────────┘                     │
│  │transform_bot│   {insight: "..."}                                     │
│  │ (format)    │                                                        │
│  └─────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Signal System](#signal-system)
- [Robot Development](#robot-development)
- [Development](#development)
- [Environment Variables](#environment-variables)

## Features

- **Composable robot swarms** — declare any combination of robots per task; `TaskComposer` auto-discovers `*_bot/` packages, no manual registration
- **Hot-reload** — PATCH a running task's config; robots stop and restart with new config, zero task downtime
- **Sleep / wake** — pause a task (preserves all stream data), resume later
- **Crash recovery** — on startup, `TaskManager` scans Redis and resumes any `PENDING`/`RUNNING` tasks
- **Real-time SSE** — dual-layer streaming: global task projections + per-task robot telemetry
- **Infinite canvas UI** — pan/zoom topology view with live robot nodes and stream counters
- **Polyglot robots** — write robots in Python or Rust; `RustRobotProxy` manages Rust subprocess lifecycle while the binary speaks Redis directly

## Architecture

```
┌─────────────────┐   REST / SSE    ┌────────────────────────┐
│  Vue 3 UI :5173 │ ◄────────────── │  FastAPI API  :8000    │
│  Infinite canvas│ ──── CRUD ────► │  /api/v1/*             │
└─────────────────┘                 └───────────┬────────────┘
                                                │ Redis Stream: commands
                                    ┌───────────▼────────────┐
                                    │      TaskManager        │
                                    │  (consumer group loop)  │
                                    └───────────┬────────────┘
                                                │ spawn
                                    ┌───────────▼────────────┐
                                    │       RobotTask         │
                                    │  ┌─────────┐ ┌───────┐ │
                                    │  │ bot A  │ │ bot B │ │
                                    │  └────┬────┘ └───┬───┘ │
                                    └───────┼──────────┼─────┘
                                            └────┬─────┘
                                    Redis Streams (per task)
                              swarmbot:task:{id}:stream:{name}
```

### Project Structure

```
swarmbot/
├── shared/       # Redis client, channel/key naming, domain models, schemas
├── robots/       # BaseRobot ABC, RustRobotProxy, TaskComposer, bot implementations
│   ├── ticker_bot/       # Example: autonomous data producer
│   ├── transform_bot/    # Example: signal-driven transformer
│   └── trading_bot/      # Example: Rust-based robot
├── worker/       # TaskManager, RobotTask, ExecutionDedupe
└── api/          # FastAPI routes, SSE bridge

frontend/src/
├── components/   # Vue 3 components (canvas, panels, cards)
├── stores/       # Pinia stores (observability, theme)
├── api/          # HTTP client and SSE subscription
└── themes/       # Multi-theme design system
```

### Task Lifecycle

```
   Create ──► PENDING ──► RUNNING ──► COMPLETED
                │             │
                │         Sleep/Wake
                │             │
                ▼             ▼
            CANCELLED     SLEEPING ──► RUNNING
                              │
                              ▼
                           FAILED
```

1. API publishes a `create` command to `swarmbot:stream:commands`
2. Worker's `TaskManager` consumes via consumer group, starts `RobotTask.run()`
3. `TaskComposer.compose()` instantiates the declared robot swarm
4. Robots emit signals to task-scoped streams (`swarmbot:task:{id}:stream:{name}`)
5. SSE bridge streams events to the frontend in real-time
6. PATCH triggers hot-reload; DELETE cancels and purges

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.12 |
| [uv](https://github.com/astral-sh/uv) | latest |
| Docker | any (for local Redis) |
| Node.js | 18+ |

### Setup

```bash
# 1. Clone and install
git clone <repo-url> && cd swarmbot
uv sync
cp .env.example .env

# 2. Start Redis
docker run --rm -p 6379:6379 redis:7

# 3. Start worker (separate terminal)
uv run python -m swarmbot.worker.main

# 4. Start API (separate terminal)
uv run uvicorn swarmbot.api.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** for the dashboard. The Vite dev server proxies `/api` to `:8000`.

## API Reference

### Task Operations

```bash
# Create a task with a robot swarm
curl -X POST http://localhost:8000/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "demo-1",
    "user_id": "u1",
    "robots": [
      {"type": "ticker_bot",    "config": {"poll_interval": 3.0, "min_value": 0, "max_value": 100}},
      {"type": "transform_bot", "config": {"multiplier": 1.5, "offset": 0.0}}
    ]
  }'

# Hot-reload config on a running task
curl -X PATCH http://localhost:8000/api/v1/tasks/demo-1 \
  -H 'Content-Type: application/json' \
  -d '{"robots": [{"type": "ticker_bot", "config": {"poll_interval": 1.0}}]}'

# Sleep / wake
curl -X POST http://localhost:8000/api/v1/tasks/demo-1/sleep
curl -X POST http://localhost:8000/api/v1/tasks/demo-1/wake

# Delete and purge all stream data
curl -X DELETE "http://localhost:8000/api/v1/tasks/demo-1?purge=true"
```

### All Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/tasks` | List all tasks |
| `POST` | `/api/v1/tasks` | Create task (publishes command) |
| `GET` | `/api/v1/tasks/{task_id}` | Get task status |
| `PATCH` | `/api/v1/tasks/{task_id}` | Update config (triggers hot-reload) |
| `DELETE` | `/api/v1/tasks/{task_id}` | Cancel and purge task |
| `POST` | `/api/v1/tasks/{task_id}/sleep` | Sleep task |
| `POST` | `/api/v1/tasks/{task_id}/wake` | Wake sleeping task |
| `GET` | `/api/v1/live/tasks` | SSE: global task projections |
| `GET` | `/api/v1/live/subscribe/{task_id}` | SSE: per-task robot telemetry |
| `GET` | `/api/v1/robots` | List available robot types |

> Append `?history=1` to the per-task SSE endpoint to include recent history on connect.

## Signal System

Robots communicate exclusively through **signals** — typed messages on task-scoped Redis Streams. A robot never calls another robot directly; it emits a signal, and any robot subscribed to that stream reacts.

### Streams

Each task has three built-in streams:

| Stream | Role | Description |
|--------|------|-------------|
| `data` | Raw data / sensor readings | Robots that generate data write here; robots that need raw input read from here |
| `output` | Processed / derived results | Robots that transform or analyze data write here; downstream bots and the frontend consume |
| `control` | System lifecycle events | Written automatically by `BaseRobot`; consumed by SSE bridge and monitoring |

The `control` stream is managed by the framework — robots automatically emit `robot_start`, `robot_stop`, and `robot_error` signals as part of their lifecycle.

### Signal Schema

Every message on a stream is a `Signal`:

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Signal type, e.g. `data_update`, `process_result` |
| `source` | `str` | `robot_type` of the sender |
| `task_id` | `str` | Owning task ID |
| `timestamp` | `str` | ISO 8601 UTC |
| `data` | `dict` | Business payload (arbitrary JSON) |
| `schema_version` | `str` | `"1.0"` — stable across producer/consumer |
| `id` | `str` | Redis Stream message ID (filled on read) |

### Signal Flow Example

```
ticker_bot                             transform_bot
    │  (autonomous — no input_streams)       │  (signal-driven — listens to data)
    │                                        │
    │ emit(DATA, data_update)                │
    └──────── data stream ──────────────────►│ on_signal("data", signal)
                                             │
                                             │ emit(OUTPUT, process_result)
                                             └──── output stream ────────► SSE Bridge ──► Frontend

Both robots automatically write to the control stream:
    robot_start / robot_stop / robot_error  ──► control stream ──► Frontend
```

### SSE Event Types

The SSE bridge maps Redis Stream signals to frontend events:

| SSE event | Triggered by | Payload highlights |
|-----------|-------------|-------------------|
| `data_update` | `data_update` signal | `robot_type`, `task_id`, `data {}` |
| `process_result` | `process_result` signal | `robot_type`, `task_id`, `data {}` |
| `robot_status` | `robot_start` / `robot_stop` / `robot_error` | `robot_type`, `state`, `last_error` |
| `task_status` | `task_status` signal | full `TaskStatus` JSON |
| `task_end` | Redis status key poll (not stream) | `task_id`, `state` |
| `heartbeat` | No messages in current poll cycle | `ts` |

> **Note:** `task_end` is synthesized by polling the Redis status key, not forwarded from the stream log. This prevents stale terminal events from replaying after sleep/wake cycles.

## Robot Development

### How Robots Work

Every robot is a subclass of `BaseRobot` — a single, universal interface. There are no predefined categories or archetypes. What makes each robot unique is how it uses signals:

- **Autonomous robots** (`input_streams = []`) — drive themselves internally. They generate data on their own schedule without subscribing to any stream. Examples: periodic data polling, sensor reading, scheduled content generation.
- **Signal-driven robots** (`input_streams = [...]`) — react to signals from other robots. They subscribe to one or more streams and process incoming data. Examples: data transformation, LLM-powered analysis, format conversion.

A robot can also be both — producing data autonomously while reacting to incoming signals. The framework imposes no constraints; `input_streams` and `output_streams` are simply declarations of which streams a robot reads from and writes to.

Whether a robot runs deterministic logic (like `1 + 1 = 2`, ensuring reliability) or AI-powered reasoning (producing creative, varied outputs) is entirely up to its implementation. Both are equally valid uses of the same `BaseRobot` base class.

### Adding a Python Robot

Create `swarmbot/robots/my_bot/` with `__init__.py` and `robot.py` — `TaskComposer` auto-discovers it.

```python
# swarmbot/robots/my_bot/robot.py
class MyBot(BaseRobot):
    robot_type = "my_bot"                        # must match directory name
    input_streams  = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
    status_broadcast_min_interval = 2.0          # throttle for high-frequency bots

    async def setup(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def teardown(self) -> None:
        self._task.cancel()
        await asyncio.gather(self._task, return_exceptions=True)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        if signal.type == SignalType.DATA_UPDATE:
            await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, {"result": ...})
        # silently skip unknown signal types

    def get_runtime_metrics(self) -> dict[str, Any]:
        return {"my_counter": self._counter}     # surfaced in frontend status
```

Then declare it in a task:

```json
{"robots": [{"type": "my_bot", "config": {"key": "value"}}]}
```

### Adding a Rust Robot

Subclass `RustRobotProxy` — Python manages process lifecycle, the Rust binary communicates with Redis directly.

```python
class TradingBot(RustRobotProxy):
    robot_type = "trading_bot"
    rust_binary = "/path/to/target/release/trading-bot"
    input_streams = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
```

The Rust process receives `TASK_ID`, `REDIS_URL`, `INPUT_STREAMS`, `OUTPUT_STREAMS`, and `BOT_*` config env vars. It must write lifecycle signals (`robot_start`/`robot_stop`/`robot_error`) to the control stream and handle `SIGTERM` for graceful shutdown.

### Adding Custom Signal Types

1. Add a value to `SignalType` in `swarmbot/shared/channels.py`
2. Add the mapping in `_signal_to_sse()` in `swarmbot/api/routes/live_stream.py`
3. Handle `signal.type == "your_type"` in the receiving robot's `on_signal()`

### Runtime Metrics

Override `get_runtime_metrics()` to expose custom counters in the frontend status panel:

```python
def get_runtime_metrics(self) -> dict[str, Any]:
    return {"processed": self._count, "last_value": self._last}
```

For high-frequency robots, set `status_broadcast_min_interval = 2.0` to throttle status pushes without slowing the signal pipeline.

## Development

```bash
# Syntax check (minimum before every commit)
uv run python -m compileall swarmbot scripts

# Lint and format
uv run ruff check --fix swarmbot scripts
uv run ruff format swarmbot scripts

# Tests
uv run pytest
uv run pytest tests/test_file.py::test_name -q
uv run pytest -x                                # stop on first failure

# Submit a demo task
uv run python scripts/publish_demo_task.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `EXECUTION_DEDUPE_TTL_SECONDS` | `300` | TTL for duplicate task execution guard |

## License

[MIT](LICENSE)
