"""Create demo task by calling the HTTP task API."""

from __future__ import annotations

import asyncio
import json
import sys
from urllib import request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

async def main() -> None:
    payload = {
        "task_id": "demo-task-1",
        "user_id": "u1",
        "robots": [
            "sample_producer",
            "sample_consumer",
        ],
        "custom_config": {
            "poll_interval": 3.0,
        },
    }

    req = request.Request(
        url="http://127.0.0.1:8000/api/v1/tasks",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _send() -> str:
        with request.urlopen(req, timeout=5) as response:
            return response.read().decode("utf-8")

    response_body = await asyncio.to_thread(_send)
    print(response_body)


if __name__ == "__main__":
    asyncio.run(main())
