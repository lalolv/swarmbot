"""任务管理器"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4
from typing import Any, Optional

from loguru import logger
from redis.exceptions import ResponseError

from pm_sports_bots.shared import (
    Channels,
    CommandReceipt,
    RedisClient,
    TaskConfig,
    TaskState,
    TaskStatus,
)
from pm_sports_bots.worker.robot_task import RobotTask


class TaskManager:
    """后台任务管理器。

    职责：
    - 监听 Redis Streams 命令流
    - 任务 CRUD（创建、取消、查询）
    - 崩溃恢复（扫描 Redis 中 PENDING/RUNNING 状态的任务）
    - 配置热更新转发
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis
        self._tasks: dict[str, RobotTask] = {}
        self._running = False
        self._command_group = "task_manager"
        self._consumer_name = f"worker-{uuid4().hex[:8]}"

    async def start(self) -> None:
        """启动任务管理器。"""
        self._running = True
        logger.info("TaskManager 已启动")

        await self._recover_tasks()
        await self._ensure_command_group()
        await self._listen_commands()

    async def stop(self) -> None:
        """停止任务管理器。"""
        self._running = False

        for task_id, task in list(self._tasks.items()):
            logger.info("正在取消任务: {}", task_id)
            task.cancel()

        if self._tasks:
            await asyncio.gather(
                *[task._task for task in self._tasks.values() if task._task],
                return_exceptions=True,
            )

        self._tasks.clear()
        logger.info("TaskManager 已停止")

    async def create_task(self, task_id: str, config: TaskConfig) -> bool:
        """创建并启动任务。"""
        if task_id in self._tasks:
            logger.warning("任务已存在: {}", task_id)
            return False

        if not config.task_id or config.task_id != task_id:
            config.task_id = task_id

        config_key = Channels.task_config(task_id)
        await self.redis.set(config_key, config.to_json(), ex=86400)
        await self.redis.sadd(Channels.all_tasks(), task_id)
        if config.user_id:
            await self.redis.sadd(Channels.user_tasks(config.user_id), task_id)

        task = RobotTask(
            task_id=task_id,
            config=config,
            redis=self.redis,
        )
        self._tasks[task_id] = task
        task._task = asyncio.create_task(self._run_task(task_id, task))
        await self._emit_task_projection(task_id)

        logger.info("任务已创建: {}", task_id)
        return True

    async def sleep_task(self, task_id: str) -> bool:
        """休眠任务（保留 Redis 数据，停止运行）。"""
        task = self._tasks.get(task_id)
        if not task:
            logger.warning("任务不存在或未运行，无法休眠: {}", task_id)
            return False
        task.sleep()
        logger.info("任务休眠请求已发送: {}", task_id)
        return True

    async def wake_task(self, task_id: str) -> bool:
        """唤醒休眠任务（重新启动运行）。"""
        if task_id in self._tasks:
            logger.warning("任务已在运行中: {}", task_id)
            return False

        config_key = Channels.task_config(task_id)
        config_data = await self.redis.get(config_key)
        if not config_data:
            logger.warning("任务配置不存在，无法唤醒: {}", task_id)
            return False

        config = TaskConfig.from_json(config_data)
        task = RobotTask(task_id=task_id, config=config, redis=self.redis)
        self._tasks[task_id] = task
        task._task = asyncio.create_task(self._run_task(task_id, task))
        await self._emit_task_projection(task_id)
        logger.info("任务已唤醒: {}", task_id)
        return True

    async def delete_task(self, task_id: str) -> bool:
        """删除任务（停止运行并清理 Redis 记录）。"""
        task = self._tasks.get(task_id)
        if task:
            task.cancel()
            if task._task:
                await asyncio.gather(task._task, return_exceptions=True)

        config_key = Channels.task_config(task_id)
        status_key = Channels.task_status(task_id)
        config_raw = await self.redis.get(config_key)
        status_raw = await self.redis.get(status_key)

        user_id = ""
        if status_raw:
            try:
                user_id = TaskStatus.from_json(status_raw).user_id
            except Exception:
                user_id = ""
        if not user_id and config_raw:
            try:
                user_id = TaskConfig.from_json(config_raw).user_id
            except Exception:
                user_id = ""

        stream_keys = [Channels.task_stream(task_id, stream) for stream in Channels.ALL_STREAMS]
        removed_key_count = await self.redis.delete(config_key, status_key, *stream_keys)
        removed_task_count = await self.redis.srem(Channels.all_tasks(), task_id)
        if user_id:
            await self.redis.srem(Channels.user_tasks(user_id), task_id)

        await self._emit_task_projection_deleted(task_id)

        logger.info(
            "任务已删除: task={} keys_removed={} task_set_removed={}",
            task_id,
            removed_key_count,
            removed_task_count,
        )
        return bool(task or removed_key_count or removed_task_count)

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态。"""
        key = Channels.task_status(task_id)
        data = await self.redis.get(key)
        if not data:
            return None
        return TaskStatus.from_json(data)

    async def list_tasks(self) -> list[TaskStatus]:
        """列出所有任务。"""
        task_ids = await self.redis.smembers(Channels.all_tasks())
        statuses = []

        for task_id in task_ids:
            status = await self.get_task_status(task_id)
            if status:
                statuses.append(status)

        return statuses

    async def _run_task(self, task_id: str, task: RobotTask) -> None:
        """运行任务并在完成后清理。"""
        try:
            await task.run()
        finally:
            self._tasks.pop(task_id, None)
            logger.info("任务已完成: {}", task_id)

    async def _recover_tasks(self) -> None:
        """恢复未完成任务（崩溃恢复）。"""
        task_ids = await self.redis.smembers(Channels.all_tasks())

        for task_id in task_ids:
            status = await self.get_task_status(task_id)
            if not status:
                continue

            if status.state not in (TaskState.PENDING, TaskState.RUNNING):
                continue

            config_key = Channels.task_config(task_id)
            config_data = await self.redis.get(config_key)
            if not config_data:
                logger.warning("任务配置不存在，跳过恢复: {}", task_id)
                continue

            config = TaskConfig.from_json(config_data)
            task = RobotTask(
                task_id=task_id,
                config=config,
                redis=self.redis,
            )
            self._tasks[task_id] = task
            task._task = asyncio.create_task(self._run_task(task_id, task))
            logger.info("任务已恢复: {}", task_id)

    async def _emit_command_receipt(
        self,
        *,
        command_id: str,
        task_id: str,
        action: str,
        status: str,
        reason: str = "",
    ) -> None:
        receipt = CommandReceipt(
            command_id=command_id,
            task_id=task_id,
            action=action,
            status=status,
            reason=reason,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        await self.redis.xadd(
            Channels.COMMAND_RECEIPT_STREAM,
            {
                "type": "command_receipt",
                "task_id": task_id,
                "timestamp": receipt.timestamp,
                "data": receipt.to_json(),
            },
            maxlen=10000,
        )

    async def _emit_task_projection(self, task_id: str) -> None:
        config_raw = await self.redis.get(Channels.task_config(task_id))
        status_raw = await self.redis.get(Channels.task_status(task_id))

        config_payload: dict[str, Any] | None = None
        robots_payload: list[dict[str, Any]] = []
        if config_raw:
            try:
                config = TaskConfig.from_json(config_raw)
                config_payload = config.to_dict()
                robots_payload = [robot.to_dict() for robot in config.robots]
            except Exception:
                config_payload = None

        status_payload: dict[str, Any] | None = None
        if status_raw:
            try:
                status_payload = TaskStatus.from_json(status_raw).to_dict()
            except Exception:
                status_payload = None

        version = await self.redis.incr(Channels.task_version(task_id))
        payload = {
            "type": "task_projection_updated",
            "task_id": task_id,
            "version": version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "snapshot": {
                "task_id": task_id,
                "status": status_payload,
                "config": config_payload,
                "robots": robots_payload,
            },
        }
        await self.redis.xadd(
            Channels.TASK_PROJECTION_STREAM,
            {
                "type": "task_projection_updated",
                "task_id": task_id,
                "timestamp": payload["timestamp"],
                "data": json.dumps(payload, ensure_ascii=False),
            },
            maxlen=10000,
        )

    async def _emit_task_projection_deleted(self, task_id: str) -> None:
        version = await self.redis.incr(Channels.task_version(task_id))
        payload = {
            "type": "task_projection_deleted",
            "task_id": task_id,
            "version": version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        await self.redis.xadd(
            Channels.TASK_PROJECTION_STREAM,
            {
                "type": "task_projection_deleted",
                "task_id": task_id,
                "timestamp": payload["timestamp"],
                "data": json.dumps(payload, ensure_ascii=False),
            },
            maxlen=10000,
        )

    async def _ensure_command_group(self) -> None:
        """确保命令消费组存在。"""
        try:
            await self.redis.xgroup_create(
                Channels.COMMAND_STREAM,
                self._command_group,
                id="$",
                mkstream=True,
            )
            logger.info(
                "命令消费组已创建: stream={} group={}",
                Channels.COMMAND_STREAM,
                self._command_group,
            )
        except ResponseError as exc:
            if "BUSYGROUP" in str(exc):
                logger.info(
                    "命令消费组已存在: stream={} group={}",
                    Channels.COMMAND_STREAM,
                    self._command_group,
                )
                return
            raise

    async def _listen_commands(self) -> None:
        """监听命令 Stream 并按消费组处理。"""
        logger.info(
            "开始监听命令流: stream={} group={} consumer={}",
            Channels.COMMAND_STREAM,
            self._command_group,
            self._consumer_name,
        )

        while self._running:
            try:
                results = await self.redis.xreadgroup(
                    group=self._command_group,
                    consumer=self._consumer_name,
                    streams={Channels.COMMAND_STREAM: ">"},
                    count=100,
                    block=1000,
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("命令流监听异常: {}", exc)
                await asyncio.sleep(1.0)
                continue

            if not results:
                continue

            for stream_name, messages in results:
                for msg_id, fields in messages:
                    if not self._running:
                        break
                    try:
                        await self._handle_command_message(fields)
                    except Exception as exc:
                        logger.error("处理命令失败 stream={} id={}: {}", stream_name, msg_id, exc)
                    finally:
                        try:
                            await self.redis.xack(Channels.COMMAND_STREAM, self._command_group, msg_id)
                        except Exception as ack_exc:
                            logger.error("命令 ACK 失败 id={}: {}", msg_id, ack_exc)

    async def _handle_command_message(self, fields: dict[str, str]) -> None:
        """处理控制消息。

        支持的 action:
        - create: 创建新任务
        - sleep: 休眠任务（保留数据）
        - wake: 唤醒休眠任务
        - delete: 删除任务（物理清理）
        - update_config: 热更新任务配置
        - shutdown: 关闭 Worker
        """
        try:
            raw = fields.get("data", "{}")
            data = json.loads(raw)
            action = data.get("action")
            task_id = data.get("task_id")
            command_id = str(data.get("command_id") or f"legacy-{datetime.utcnow().timestamp()}")
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}

            if action and task_id:
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="accepted",
                )

            if action == "create" and task_id:
                raw_config_data = payload.get("config") if payload else data.get("config", {})
                if not isinstance(raw_config_data, dict):
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="配置格式错误",
                    )
                    return
                config_data: dict[str, Any] = dict(raw_config_data)
                user_id = (payload.get("user_id") if payload else data.get("user_id", "")) or ""
                if user_id and "user_id" not in config_data:
                    config_data["user_id"] = user_id
                config = TaskConfig.from_dict(config_data)
                created = await self.create_task(task_id, config)
                if not created:
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="任务已存在或正在运行",
                    )
                    return
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="applied",
                )

            elif action == "sleep" and task_id:
                slept = await self.sleep_task(task_id)
                if not slept:
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="任务不存在或未运行",
                    )
                    return
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="applied",
                )

            elif action == "wake" and task_id:
                waked = await self.wake_task(task_id)
                if not waked:
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="任务无法唤醒（不存在或已运行）",
                    )
                    return
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="applied",
                )

            elif action == "delete" and task_id:
                deleted = await self.delete_task(task_id)
                if not deleted:
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="任务不存在",
                    )
                    return
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="applied",
                )

            elif action == "update_config" and task_id:
                raw_patch = payload.get("patch") if payload else data.get("patch", {})
                if not isinstance(raw_patch, dict):
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="patch 格式错误",
                    )
                    return
                patch: dict[str, Any] = dict(raw_patch)
                task = self._tasks.get(task_id)
                if not task:
                    logger.warning("任务未运行，无法更新配置: {}", task_id)
                    await self._emit_command_receipt(
                        command_id=command_id,
                        task_id=task_id,
                        action=action,
                        status="rejected",
                        reason="任务未运行，无法更新配置",
                    )
                    return
                await task.update_config(patch)
                logger.info("任务配置已更新: {}", task_id)
                await self._emit_task_projection(task_id)
                await self._emit_command_receipt(
                    command_id=command_id,
                    task_id=task_id,
                    action=action,
                    status="applied",
                )

            elif action == "shutdown":
                logger.info("收到关闭指令")
                self._running = False

            else:
                logger.warning("未知控制消息: {}", data)

        except Exception as exc:
            logger.error("处理控制消息失败: {}", exc)
