"""Robot 任务编排器。"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from pm_sports_bots.shared import RedisClient, TaskConfig

from .base import BaseRobot
from .sample_producer import SampleProducer
from .sample_consumer import SampleConsumer


class TaskComposer:
    """根据 TaskConfig 创建并管理机器人。

    # 🔧 自定义点: 在 compose() 中添加新机器人的实例化逻辑
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis
        self._robots: dict[str, list[BaseRobot]] = {}
        self._robot_tasks: dict[str, list[asyncio.Task[None]]] = {}

    def compose(self, task_id: str, config: TaskConfig) -> list[BaseRobot]:
        """根据配置创建任务对应的机器人列表。

        # 🔧 自定义点: 添加条件创建逻辑
        """
        cfg = config.to_dict()
        robots: list[BaseRobot] = [
            SampleProducer(task_id, self.redis, cfg),
            SampleConsumer(task_id, self.redis, cfg),
        ]

        self._robots[task_id] = robots
        logger.info("编排器已创建 {} 个机器人: task={}", len(robots), task_id)
        return robots

    async def start_all(self, task_id: str) -> list[asyncio.Task[None]]:
        """启动任务的所有机器人。"""
        robots = self._robots.get(task_id, [])
        tasks: list[asyncio.Task[None]] = []
        for robot in robots:
            tasks.append(
                asyncio.create_task(
                    robot.run_loop(),
                    name=f"robot:{task_id}:{robot.robot_type}",
                )
            )
        self._robot_tasks[task_id] = tasks
        return tasks

    async def stop_all(self, task_id: str) -> None:
        """停止任务的所有机器人。"""
        for robot in self._robots.get(task_id, []):
            await robot.stop()

        tasks = self._robot_tasks.pop(task_id, [])
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        self._robots.pop(task_id, None)

    def get_robots(self, task_id: str) -> list[BaseRobot]:
        """查询任务机器人列表。"""
        return self._robots.get(task_id, [])
