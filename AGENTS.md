# AGENTS.md
Guidance for coding agents working in `pm-sports-bots`.

## 1) Project Snapshot
- Language: Python 3.12+
- Package/runtime: `uv`
- Stack: FastAPI + Redis (asyncio) + Loguru
- Main package: `pm_sports_bots/`
- API entry: `pm_sports_bots.api.main:app`
- Worker entry: `pm_sports_bots.worker.main`

## 2) Cursor/Copilot Rules
- `.cursor/rules/`: not found
- `.cursorrules`: not found
- `.github/copilot-instructions.md`: not found
- No Cursor/Copilot rule files are currently present.

## 3) Environment Setup
- Python version is pinned in `.python-version` (`3.12`).
- Install dependencies:
```bash
uv sync
```
- Prepare local env file:
```bash
cp .env.example .env
```
- Default env values:
  - `REDIS_URL=redis://localhost:6379/0`
  - `EXECUTION_DEDUPE_TTL_SECONDS=300`
- Start Redis locally when needed:
```bash
docker run --rm -p 6379:6379 redis:7
```

## 4) Run Commands
- Start worker:
```bash
uv run python -m pm_sports_bots.worker.main
```
- Start API with reload:
```bash
uv run uvicorn pm_sports_bots.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Publish demo task:
```bash
uv run python scripts/publish_demo_task.py
```

## 5) Build, Lint, and Test Commands
The repo does not currently pin lint/test tools in `pyproject.toml`; use these operational defaults.

### Build / sanity
- Syntax compile check:
```bash
uv run python -m compileall pm_sports_bots scripts
```

### Lint / format
- Lint (if `ruff` is installed):
```bash
uv run ruff check pm_sports_bots scripts
```
- Format (if `ruff format` is installed):
```bash
uv run ruff format pm_sports_bots scripts
```

### Tests (pytest)
- Run all tests:
```bash
uv run pytest
```
- Run one test file:
```bash
uv run pytest tests/test_example.py
```
- Run one test function (recommended pattern):
```bash
uv run pytest tests/test_example.py::test_specific_behavior -q
```
- Run one class method:
```bash
uv run pytest tests/test_example.py::TestExample::test_specific_behavior -q
```

## 6) Code Style and Conventions

### Imports
- Use 3 groups with one blank line between: stdlib, third-party, local.
- Prefer absolute imports from `pm_sports_bots...`.
- Keep imports at module top unless local import prevents cycles/heavy imports.

### Formatting
- Follow PEP 8 and nearby file style.
- Keep functions small and focused.
- Use docstrings for modules, classes, and public functions.
- Existing docs/comments are often Chinese; follow surrounding language.

### Typing
- Use modern annotations (`str | None`, `list[str]`, `dict[str, Any]`).
- Type public APIs and important internal helpers.
- Prefer specific types; keep `Any` at dynamic boundaries only.
- Use Pydantic models for API payloads.
- Use dataclasses for internal state/domain records.

### Naming
- `snake_case`: functions, methods, variables, modules
- `PascalCase`: classes
- `UPPER_SNAKE_CASE`: constants
- Keep Redis key/channel naming centralized in `Channels`.

### Async and Concurrency
- This is an async-first codebase; avoid blocking calls.
- Use `asyncio.to_thread(...)` for unavoidable blocking I/O.
- Manage background tasks explicitly (create/cancel/await cleanup).
- Handle `asyncio.CancelledError` separately when shutting down loops.

### Error Handling
- API routes should raise `HTTPException` with meaningful status codes/details.
- Worker/runtime loops should catch, log context, and continue or fail clearly.
- Preserve exception chaining (`raise ... from exc`) when re-raising.
- Avoid silent failures except intentional best-effort cleanup.

### Logging
- Use `loguru.logger`.
- Include context (`task_id`, `robot_type`, `stream`, `stage`) in logs.

### Redis / Streams
- Prefer the `RedisClient` wrapper over raw Redis client calls.
- Keep Stream payload schema stable and JSON-serialized.
- When adding a new stream, update both `Channels.ALL_STREAMS` and SSE mapping.
- Keep TTL behavior explicit for task config/status keys.

### API Patterns
- Routes should live under `/api/v1/...`.
- Request/response models should be explicit Pydantic models.
- Validate patch/update payload shape before merge.
- Keep response shapes consistent (`accepted`, `task_id`, etc.).

### Robot Patterns
- New robots should extend `BaseRobot`.
- Define `robot_type`, `input_streams`, `output_streams`, `setup`, `on_signal`.
- Emit lifecycle signals consistently (`robot_start`, `robot_stop`, `robot_error`).
- Keep orchestration and robot registry changes in `TaskComposer`.

## 7) Agent Guardrails
- Make minimal, targeted changes; avoid broad refactors unless asked.
- Preserve architecture split: `api/`, `worker/`, `robots/`, `shared/`.
- Never commit secrets (`.env`, keys, credentials, tokens).
- Do not edit `.venv/` or cache artifacts.
- If you add lint/test tooling, update this file with exact commands.

## 8) Pre-PR Checklist
- `uv sync` run if dependencies changed
- Syntax check run (`compileall` minimum)
- Lint run (if configured)
- Tests run, or reason clearly documented
- API and worker startup paths still valid
- `README.md` / `AGENTS.md` updated when behavior/commands changed
