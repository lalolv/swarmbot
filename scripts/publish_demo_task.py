"""Publish a demo create-task command to the control channel."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pm_sports_bots.shared import Channels, RedisClient


async def main() -> None:
    redis = RedisClient()
    await redis.connect()
    try:
        payload = {
            "action": "create",
            "task_id": "demo-task-1",
            "config": {"user_id": "u1"},
        }
        await redis.publish(Channels.CONTROL, json.dumps(payload, ensure_ascii=False))
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
