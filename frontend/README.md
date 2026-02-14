# Frontend Observability Console

Vue 3 + Tailwind frontend with only two core capabilities:

1. Create task
2. Monitor task in infinite canvas

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Backend API is proxied to `http://127.0.0.1:8000` by Vite. You can override base URL:

```bash
VITE_API_BASE=http://127.0.0.1:8000 npm run dev
```

## Current UI Design

The UI is intentionally minimal and centered around one workflow:

1. Fill create-task form (`task_id`, `user_id`, `poll_interval`, `robots`).
2. Click **Create & Monitor**.
3. Observe task/robot runtime from one infinite canvas.

The monitor panel exposes:

- Task state + SSE connection state
- Robot count + total event count
- Stream counters (`data`, `output`, `control`)
- Canvas topology with robot nodes and stream hubs

## Infinite Canvas Assessment

This project includes an **Infinite Canvas** view (`ef-infinite-canvas`) for topology-style inspection.

### Why it fits

- Good for large robot graphs (many nodes, pan/zoom exploration).
- Useful when streams become non-linear or dynamic.
- Better at preserving spatial context than flat tables.

### Limitations now

- Current backend SSE payload for `data_update` / `process_result` does not include explicit robot source in event payload, so edge inference is limited.
- Canvas currently visualizes robot state/activity, but not full stream causality.

### Recommended next backend fields (for stronger canvas)

When emitting stream signals, include these fields in payload or SSE mapping:

- `robot_type` (source)
- `target_robot_type` (if known)
- `stream`
- `latency_ms`
- `trace_id`

With these fields, canvas can support directional edges, latency heatmap, and replay path tracking.

## Suggested Next Iteration

1. Add a backend endpoint for current robot graph metadata (nodes + declared stream subscriptions).
2. Extend SSE mapping to keep `source` from stream fields in frontend payload.
3. Add brush/lasso selection in canvas for filtering timeline by selected robots.
