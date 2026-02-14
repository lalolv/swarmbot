# AGENTS.md
Operational guidance for coding agents working in `pm-sports-bots`.

## 1) Repository Snapshot
- Language/runtime: Python `3.12` + `uv`
- Core stack: FastAPI, Redis (async), Loguru
- Main package: `pm_sports_bots/`
- API app entry: `pm_sports_bots.api.main:app`
- Worker entry: `python -m pm_sports_bots.worker.main`
- Architecture split: `api/`, `worker/`, `robots/`, `shared/`

## 2) Cursor/Copilot Rule Files
- `.cursor/rules/`: not present
- `.cursorrules`: not present
- `.github/copilot-instructions.md`: not present
- No extra IDE agent rule files are active right now.
- If any of these files are added later, treat them as higher-priority local guidance.

## 3) Environment Setup
- Python is pinned in `.python-version` (`3.12`).
- Install dependencies: `uv sync`
- Prepare local env file: `cp .env.example .env`
- Default env values used by scaffold:
  - `REDIS_URL=redis://localhost:6379/0`
  - `EXECUTION_DEDUPE_TTL_SECONDS=300`
- Start local Redis when needed: `docker run --rm -p 6379:6379 redis:7`

## 4) Local Run Commands
- Start worker: `uv run python -m pm_sports_bots.worker.main`
- Start API with reload: `uv run uvicorn pm_sports_bots.api.main:app --host 0.0.0.0 --port 8000 --reload`
- Publish demo task: `uv run python scripts/publish_demo_task.py`

## 5) Build, Lint, and Test Commands
The project currently does not pin lint/test tooling in `pyproject.toml`; use these defaults.

### Build / Sanity
- Syntax compile check (minimum): `uv run python -m compileall pm_sports_bots scripts`

### Lint / Format (when Ruff is available)
- Lint: `uv run ruff check pm_sports_bots scripts`
- Auto-fix lint issues: `uv run ruff check --fix pm_sports_bots scripts`
- Format: `uv run ruff format pm_sports_bots scripts`

### Tests (pytest)
- Run full suite: `uv run pytest`
- Run a single test file: `uv run pytest tests/test_example.py`
- Run a single test function (recommended pattern):
  - `uv run pytest tests/test_example.py::test_specific_behavior -q`
- Run a single test class method:
  - `uv run pytest tests/test_example.py::TestExample::test_specific_behavior -q`
- Run tests by expression filter:
  - `uv run pytest -k "task_manager and not slow" -q`
- Stop fast on first failure: `uv run pytest -x`

Note: there is no `tests/` directory in the current scaffold. Keep the single-test command patterns above for future tests.

## 6) Code Style and Conventions

### Imports
- Use three import groups with one blank line: stdlib, third-party, local.
- Prefer absolute imports from `pm_sports_bots...`.
- Keep imports at module top unless a local import prevents cycles/heavy startup cost.
- Avoid wildcard imports.

### Formatting
- Follow PEP 8 plus surrounding file style.
- Keep functions focused and small; split deeply nested logic.
- Add docstrings for modules, classes, and public functions.
- Existing comments/docstrings are often Chinese; match nearby language.
- Use ASCII by default; keep existing Unicode text if the file already uses it.

### Typing
- Use modern type hints (`str | None`, `list[str]`, `dict[str, Any]`).
- Type public APIs and critical internal helpers.
- Prefer concrete types over `Any`; reserve `Any` for dynamic boundaries.
- Use Pydantic models for API request/response schemas.
- Use `@dataclass` for internal domain/state records.

### Naming
- `snake_case`: variables, functions, methods, modules.
- `PascalCase`: classes.
- `UPPER_SNAKE_CASE`: constants.
- Keep Redis key/channel naming centralized in `Channels`.
- Robot identifiers should remain stable (`robot_type` values are contract-like).

### Async and Concurrency
- This is an async-first codebase; avoid blocking I/O in async paths.
- Use `asyncio.to_thread(...)` for unavoidable blocking calls.
- Manage background tasks explicitly (create, cancel, and await cleanup).
- Handle `asyncio.CancelledError` separately for graceful shutdown.
- Do not swallow cancellation or shutdown exceptions silently.

### Error Handling
- API handlers should raise `HTTPException` with meaningful status and detail.
- Validate payload shape before merge/update operations.
- In worker/runtime loops, catch exceptions, log context, and continue/fail clearly.
- Preserve exception chaining when re-raising (`raise ... from exc`).
- Use best-effort cleanup blocks, but log failures.

### Logging
- Use `loguru.logger` consistently.
- Include key context when possible: `task_id`, `robot_type`, `stream`, `stage`.
- Keep messages actionable; avoid noisy per-iteration logs unless debugging.

### Redis / Stream Contracts
- Prefer `RedisClient` wrapper over raw Redis client usage.
- Keep stream payload schema stable and JSON serialized.
- Use `ensure_ascii=False` where current code does so for payload compatibility.
- If adding a stream, update `Channels.ALL_STREAMS` and SSE bridge mapping together.
- Keep TTL behavior explicit for task config/status/dedupe keys.

### API Patterns
- Routes live under `/api/v1/...`.
- Keep request and response models explicit.
- Maintain consistent response envelopes (`accepted`, `task_id`, `message`, etc.).
- Keep route modules thin; move orchestration/business logic to worker/robots/shared layers.

### Robot Patterns
- New robots must extend `BaseRobot`.
- Implement required members: `robot_type`, `input_streams`, `output_streams`, `setup`, `on_signal`.
- Optional hooks: `teardown`, `on_tick`, `tick_interval`, `get_runtime_metrics`.
- Emit lifecycle signals consistently: `robot_start`, `robot_stop`, `robot_error`.
- Register robot types through `TaskComposer` updates.

## 7) Agent Guardrails
- Make minimal, targeted changes; avoid broad refactors unless requested.
- Preserve current architecture boundaries (`api`, `worker`, `robots`, `shared`).
- Never commit secrets (`.env`, keys, tokens, credentials).
- Do not edit `.venv/`, cache directories, or generated artifacts unless asked.
- If you introduce tooling changes, update this file with exact commands.

## 8) Pre-PR / Pre-Commit Checklist
- Sync dependencies if needed: `uv sync`
- Run syntax sanity check (`compileall` minimum)
- Run lint/format when configured
- Run relevant tests (or state why tests were not run)
- Verify API and worker startup commands still work
- Update `README.md` and `AGENTS.md` when behavior or workflow changes

## 9) Verification Workflow for Agents
- For small edits: run at least `uv run python -m compileall pm_sports_bots scripts`.
- For behavior changes: run focused pytest commands first, then broader suite when available.
- Prefer single-test execution while iterating, then run `uv run pytest -x` before handoff.
- If no tests exist for touched code, state that explicitly and include manual verification steps.
- When touching stream contracts, verify both producer and consumer sides still parse payloads.

## 10) Common Pitfalls to Avoid
- Do not bypass `TaskComposer` registration when introducing new robot types.
- Do not add new Redis stream names without updating `Channels.ALL_STREAMS`.
- Do not change response envelope fields without checking existing API clients.
- Do not introduce blocking SDK/network calls directly inside async loops.
- Do not remove Chinese comments/docstrings in files that already use them unless requested.
