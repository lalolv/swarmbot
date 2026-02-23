## PM Sports Bots Scaffold

Redis Streams + Worker + SSE backend scaffold is ready under `swarmbot/`.

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
uv run python -m swarmbot.worker.main
```

### 4) Start API (task CRUD + SSE bridge)

```bash
uv run uvicorn swarmbot.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5) Submit a demo task

```bash
uv run python scripts/publish_demo_task.py
```

### 6) Task APIs

`robots` 是任务编排的必填字段（至少 1 个），每个元素使用对象格式：
`{"type": "...", "enabled": true, "config": {...}}`。

Create task:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H 'content-type: application/json' \
  -d '{
    "task_id": "demo-task-1",
    "user_id": "u1",
    "robots": [
      {"type": "ticker_bot", "config": {"poll_interval": 3.0, "min_value": 0, "max_value": 100}},
      {"type": "transform_bot", "config": {"multiplier": 1.5, "offset": 0.0}}
    ],
    "custom_config": {}
  }'
```

Update running task config (supports hot-reload robots):

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tasks/demo-task-1 \
  -H 'content-type: application/json' \
  -d '{"robots": [{"type": "ticker_bot", "config": {"poll_interval": 1.0}}]}'
```

Delete task (purge data):

```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/tasks/demo-task-1?purge=true"
```

### 7) Subscribe SSE

Open:

`http://127.0.0.1:8000/api/v1/live/subscribe/demo-task-1?history=1`

### 8) Frontend observability console (Vue3 + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

### Environment

- `REDIS_URL` default: `redis://localhost:6379/0`
- `EXECUTION_DEDUPE_TTL_SECONDS` default: `300`
