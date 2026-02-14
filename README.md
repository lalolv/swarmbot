## PM Sports Bots Scaffold

Redis Streams + Worker + SSE backend scaffold is ready under `pm_sports_bots/`.

### 1) Install dependencies

```bash
uv sync
```

### 1.5) Prepare env file

```bash
cp .env.example .env
```

### 2) Start Redis (if local)

```bash
docker run --rm -p 6379:6379 redis:7
```

### 3) Start Worker

```bash
uv run python -m pm_sports_bots.worker.main
```

### 4) Start API (SSE bridge)

```bash
uv run uvicorn pm_sports_bots.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5) Submit a demo task

```bash
uv run python scripts/publish_demo_task.py
```

### 6) Subscribe SSE

Open:

`http://127.0.0.1:8000/api/v1/live/subscribe/demo-task-1?history=1`

### Environment

- `REDIS_URL` default: `redis://localhost:6379/0`
- `EXECUTION_DEDUPE_TTL_SECONDS` default: `300`
