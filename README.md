<div align="center">

# Swarmbot

**Redis Streams · FastAPI · Vue 3 · Real-time Robot Orchestration**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)

[中文文档](./README.zh.md)

</div>

---

## Overview

Swarmbot is a scaffold for managing fleets of autonomous robots that execute tasks asynchronously. Each task composes one or more robots; robots communicate through Redis Streams and stream live telemetry to a Vue 3 dashboard via Server-Sent Events.

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
                                    │  │ ticker  │ │transf │ │
                                    │  └────┬────┘ └───┬───┘ │
                                    └───────┼──────────┼─────┘
                                            └────┬─────┘
                                    Redis Streams (per task)
                              swarmbot:task:{id}:stream:{name}
```

## Features

- **Composable robots** — declare any combination of robots per task; `TaskComposer` auto-discovers `*_bot/` packages, no manual registration
- **Hot-reload** — PATCH a running task's config; robots stop and restart with the new config, no task restart
- **Sleep / wake** — pause a task (preserves all stream data), resume it later
- **Crash recovery** — on worker startup, `TaskManager` scans Redis and resumes any `PENDING`/`RUNNING` tasks
- **Real-time SSE** — dual-layer streaming: global task projections feed + per-task robot telemetry
- **Infinite canvas UI** — pan/zoom topology view with robot nodes and live stream counters
- **Rust robot support** — subclass `RustRobotProxy`; Python manages process lifecycle, Rust binary speaks Redis directly

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.12 |
| [uv](https://github.com/astral-sh/uv) | latest |
| Docker | any (for local Redis) |
| Node.js | 18+ |

## Quick Start

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

Open **http://localhost:5173** for the dashboard. The Vite dev server proxies `/api` → `:8000`.

## API Reference

### Tasks

```bash
# Create a task (robots field is required)
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

### SSE Streams

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/live/tasks` | Global task projection feed (all state changes) |
| `GET /api/v1/live/subscribe/{task_id}` | Per-task robot telemetry stream |
| `GET /api/v1/live/subscribe/{task_id}?history=1` | Include recent history on connect |

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/tasks` | List all tasks |
| `GET` | `/api/v1/tasks/{task_id}` | Get task status |
| `GET` | `/api/v1/robots` | List available robot types |

## Signal System

Every robot can both **emit** signals and **receive** signals. Communication happens exclusively through Redis Streams scoped to the task.

### Streams

Each task has three built-in streams:

| Stream | Role | Default producers | Default consumers |
|--------|------|-------------------|-------------------|
| `data` | Raw data / sensor readings | Pure-producer bots | Transformer bots |
| `output` | Processed / derived results | Transformer bots | Downstream bots, frontend |
| `control` | System lifecycle events | `BaseRobot` (automatic) | SSE bridge, monitoring |

The control stream is written automatically — you never emit to it directly. Every robot emits `robot_start`, `robot_stop`, and `robot_error` signals here as part of its lifecycle.

### Signal Fields

Every message on a stream is a `Signal`:

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Signal type, e.g. `data_update`, `process_result` |
| `source` | `str` | `robot_type` of the sender |
| `task_id` | `str` | Owning task ID |
| `timestamp` | `str` | ISO 8601 UTC |
| `data` | `dict` | Business payload (arbitrary JSON) |
| `schema_version` | `str` | `"1.0"` — keep stable across producer/consumer |
| `id` | `str` | Redis Stream message ID (filled on read) |

### Two Robot Archetypes

**Pure Producer** — generates data, subscribes to nothing:

```
ticker_bot
  setup() → asyncio.create_task(_tick_loop())
  _tick_loop():
    while not cancelled:
      emit(DATA, DATA_UPDATE, {"value": 42.0, ...})  ──► data stream
      sleep(poll_interval)
```

```python
class TickerBot(BaseRobot):
    robot_type = "ticker_bot"
    input_streams  = []                  # no subscriptions
    output_streams = [StreamName.DATA]

    async def setup(self) -> None:
        self._tick = asyncio.create_task(self._tick_loop())

    async def teardown(self) -> None:
        self._tick.cancel()
        await asyncio.gather(self._tick, return_exceptions=True)

    async def _tick_loop(self) -> None:
        while not self._cancelled:
            await self.emit(StreamName.DATA, SignalType.DATA_UPDATE, {"value": ...})
            await asyncio.sleep(float(self.robot_config.get("poll_interval", 5.0)))
```

**Transformer** — reacts to incoming signals, produces derived results:

```
transform_bot
  run_loop() xread(data stream) ──► on_signal()
    signal.type == DATA_UPDATE:
      emit(OUTPUT, PROCESS_RESULT, {"result": ...})  ──► output stream
```

```python
class TransformBot(BaseRobot):
    robot_type = "transform_bot"
    input_streams  = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]

    async def setup(self) -> None:
        pass  # stateless; run_loop drives everything

    async def on_signal(self, stream: str, signal: Signal) -> None:
        if signal.type == SignalType.DATA_UPDATE:
            value = float(signal.data["value"])
            result = value * float(self.robot_config.get("multiplier", 1.5))
            await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, {"result": result})
        # unknown types are silently ignored
```

### Demo Signal Flow

```
ticker_bot                             transform_bot
    │                                       │
    │ emit(DATA, data_update)               │
    └──────── data stream ─────────────────►│ on_signal("data", signal)
                                            │
                                            │ emit(OUTPUT, process_result)
                                            └──── output stream ────────► SSE Bridge ──► Frontend
                                                                                    (process_result event)
Both robots automatically write to the control stream:
    robot_start / robot_stop / robot_error  ──► control stream ──► Frontend (robot_status event)
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

> **Note:** `task_end` is never forwarded from the stream log. The bridge polls the Redis status key to synthesize it, so sleep/wake cycles don't replay stale terminal events.

### Adding Custom Signal Types

1. Add a value to `SignalType` in `swarmbot/shared/channels.py`
2. Add the mapping in `_signal_to_sse()` in `swarmbot/api/routes/live_stream.py`
3. Handle `signal.type == "your_type"` in the receiving robot's `on_signal()`

### Status Broadcast and Runtime Metrics

On every `emit()` call and every received signal, the robot pushes a status snapshot to the frontend. Override `get_runtime_metrics()` to include custom counters in that snapshot:

```python
def get_runtime_metrics(self) -> dict[str, Any]:
    return {"processed": self._count, "last_value": self._last}
```

For high-frequency robots (e.g. trading bots processing thousands of signals/sec), set `status_broadcast_min_interval = 2.0` to throttle status pushes without slowing the signal pipeline.

## Adding a Robot

Create `swarmbot/robots/my_bot/` with `__init__.py` and `robot.py` — `TaskComposer` will find it automatically.

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

## Development

```bash
# Syntax check (minimum before every commit)
uv run python -m compileall swarmbot scripts

# Lint and format
uv run ruff check --fix swarmbot scripts
uv run ruff format swarmbot scripts

# Tests (no suite yet — patterns for when you add them)
uv run pytest
uv run pytest tests/test_file.py::test_name -q
uv run pytest -x                                # stop on first failure

# Submit a demo task via script
uv run python scripts/publish_demo_task.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `EXECUTION_DEDUPE_TTL_SECONDS` | `300` | TTL for duplicate task execution guard |
