"""FastAPI app entry for live stream bridge."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from swarmbot.api.routes.live_stream import router as live_router
from swarmbot.api.routes.tasks import router as task_router
from swarmbot.shared import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = RedisClient()
    await redis.connect()
    app.state.redis = redis
    app.state.shutting_down = False
    try:
        yield
    finally:
        app.state.shutting_down = True
        await redis.close()


app = FastAPI(title="PM Sports Bots API", lifespan=lifespan)
app.include_router(live_router)
app.include_router(task_router)
