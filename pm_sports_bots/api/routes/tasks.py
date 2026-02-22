"""Task management APIs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from pm_sports_bots.api.schemas.tasks import CreateTaskRequest, RobotSpec, UpdateTaskRequest
from pm_sports_bots.robots import TaskComposer
from pm_sports_bots.shared import (
    Channels,
    RedisClient,
    TaskCommand,
    TaskConfig,
    TaskState,
    TaskStatus,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _redis_from_request(request: Request) -> RedisClient:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RuntimeError("Redis client missing in app state")
    return redis


def _serialize_robot_specs(robots: list[RobotSpec]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for item in robots:
        serialized.append(item.model_dump())
    return serialized


def _validate_robot_types(robots: list[dict[str, Any]]) -> None:
    available = set(TaskComposer.available_robot_types())
    for spec in robots:
        robot_type = spec.get("type")
        if robot_type not in available:
            available_text = ", ".join(sorted(available))
            raise HTTPException(
                status_code=422,
                detail=f"Unknown robot type: {robot_type}. Available: {available_text}",
            )


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(current, value)
        else:
            merged[key] = value
    return merged


async def _load_task_detail(redis: RedisClient, task_id: str) -> dict[str, Any]:
    status_key = Channels.task_status(task_id)
    config_key = Channels.task_config(task_id)
    status_raw = await redis.get(status_key)
    config_raw = await redis.get(config_key)

    status_payload: dict[str, Any] | None = None
    if status_raw:
        try:
            status_payload = TaskStatus.from_json(status_raw).to_dict()
        except Exception:
            status_payload = None

    config_payload: dict[str, Any] | None = None
    robots_payload: list[dict[str, Any]] = []
    if config_raw:
        try:
            config = TaskConfig.from_json(config_raw)
            config_payload = config.to_dict()
            robots_payload = [robot.to_dict() for robot in config.robots]
        except Exception:
            config_payload = None

    return {
        "task_id": task_id,
        "status": status_payload,
        "config": config_payload,
        "robots": robots_payload,
    }


async def _enqueue_command(
    redis: RedisClient,
    *,
    task_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
) -> TaskCommand:
    command = TaskCommand.create(task_id=task_id, action=action, payload=payload)
    encoded = command.to_json()
    await redis.xadd(
        Channels.COMMAND_STREAM,
        {
            "type": "task_command",
            "task_id": task_id,
            "timestamp": command.created_at,
            "data": encoded,
        },
        maxlen=5000,
    )
    return command


@router.get("/robots")
async def list_available_robots() -> dict[str, Any]:
    return {"robot_types": TaskComposer.available_robot_types()}


@router.post("")
async def create_task(request: Request, body: CreateTaskRequest) -> dict[str, Any]:
    redis = _redis_from_request(request)
    task_id = body.task_id or f"task-{uuid4().hex[:8]}"

    if await redis.exists(Channels.task_config(task_id)) or await redis.exists(Channels.task_status(task_id)):
        raise HTTPException(status_code=409, detail=f"Task already exists: {task_id}")

    serialized_robots = _serialize_robot_specs(body.robots)
    _validate_robot_types(serialized_robots)

    config_payload = {
        "task_id": task_id,
        "user_id": body.user_id,
        "name": body.name,
        "description": body.description,
        "robots": serialized_robots,
        "custom_config": dict(body.custom_config),
    }
    command = await _enqueue_command(
        redis,
        task_id=task_id,
        action="create",
        payload={
            "user_id": body.user_id,
            "config": config_payload,
        },
    )
    return {
        "task_id": task_id,
        "command_id": command.command_id,
        "accepted": True,
        "message": "Create command published",
    }


@router.get("")
async def list_tasks(request: Request) -> dict[str, Any]:
    redis = _redis_from_request(request)
    task_ids = sorted(await redis.smembers(Channels.all_tasks()))
    tasks: list[dict[str, Any]] = []
    for task_id in task_ids:
        exists = await redis.exists(Channels.task_config(task_id)) or await redis.exists(Channels.task_status(task_id))
        if not exists:
            await redis.srem(Channels.all_tasks(), task_id)
            continue
        tasks.append(await _load_task_detail(redis, task_id))
    return {
        "items": tasks,
        "count": len(tasks),
    }


@router.get("/{task_id}")
async def get_task(task_id: str, request: Request) -> dict[str, Any]:
    redis = _redis_from_request(request)
    exists = await redis.exists(Channels.task_config(task_id)) or await redis.exists(Channels.task_status(task_id))
    if not exists:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return await _load_task_detail(redis, task_id)


@router.patch("/{task_id}")
async def update_task(task_id: str, request: Request, body: UpdateTaskRequest) -> dict[str, Any]:
    redis = _redis_from_request(request)
    status_raw = await redis.get(Channels.task_status(task_id))
    if not status_raw:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    try:
        status = TaskStatus.from_json(status_raw)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Task status broken: {task_id}") from exc

    if status.state not in {TaskState.PENDING, TaskState.RUNNING}:
        raise HTTPException(status_code=409, detail=f"Task is not active: {task_id} ({status.state.value})")

    config_raw = await redis.get(Channels.task_config(task_id))
    if not config_raw:
        raise HTTPException(status_code=409, detail=f"Task config missing: {task_id}")

    try:
        current_config = TaskConfig.from_json(config_raw)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Task config broken: {task_id}") from exc

    patch = dict(body.patch)
    if "robots" in patch:
        raise HTTPException(status_code=422, detail="Use top-level 'robots' field instead of patch.robots")

    if body.robots is not None:
        patch["robots"] = _serialize_robot_specs(body.robots)

    if not patch:
        raise HTTPException(status_code=422, detail="Empty patch")

    merged_payload = _deep_merge_dict(current_config.to_dict(), patch)
    try:
        merged_config = TaskConfig.from_dict(merged_payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    _validate_robot_types([robot.to_dict() for robot in merged_config.robots])

    command = await _enqueue_command(
        redis,
        task_id=task_id,
        action="update_config",
        payload={"patch": patch},
    )
    return {
        "task_id": task_id,
        "command_id": command.command_id,
        "accepted": True,
        "message": "Update command published",
    }


@router.delete("/{task_id}")
async def delete_task(task_id: str, request: Request) -> dict[str, Any]:
    redis = _redis_from_request(request)
    exists = await redis.exists(Channels.task_config(task_id)) or await redis.exists(Channels.task_status(task_id))
    if not exists:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    command = await _enqueue_command(redis, task_id=task_id, action="delete")
    return {
        "task_id": task_id,
        "command_id": command.command_id,
        "accepted": True,
        "message": "Delete command published",
    }


@router.post("/{task_id}/sleep")
async def sleep_task(task_id: str, request: Request) -> dict[str, Any]:
    redis = _redis_from_request(request)
    status_raw = await redis.get(Channels.task_status(task_id))
    if not status_raw:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    try:
        status = TaskStatus.from_json(status_raw)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Task status broken: {task_id}") from exc

    if status.state != TaskState.RUNNING:
        raise HTTPException(status_code=409, detail=f"Task is not running: {task_id} ({status.state.value})")

    command = await _enqueue_command(redis, task_id=task_id, action="sleep")
    return {
        "task_id": task_id,
        "command_id": command.command_id,
        "accepted": True,
        "message": "Sleep command published",
    }


@router.post("/{task_id}/wake")
async def wake_task(task_id: str, request: Request) -> dict[str, Any]:
    redis = _redis_from_request(request)
    status_raw = await redis.get(Channels.task_status(task_id))
    if not status_raw:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    try:
        status = TaskStatus.from_json(status_raw)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Task status broken: {task_id}") from exc

    if status.state != TaskState.SLEEPING:
        raise HTTPException(status_code=409, detail=f"Task is not sleeping: {task_id} ({status.state.value})")

    command = await _enqueue_command(redis, task_id=task_id, action="wake")
    return {
        "task_id": task_id,
        "command_id": command.command_id,
        "accepted": True,
        "message": "Wake command published",
    }
