"""Robot 任务编排器。

自动扫描 robots/*_bot/ 子目录，发现并注册所有 BaseRobot 子类。
新增机器人只需创建 xxx_bot/ 目录并在 robot.py 中声明类，无需修改此文件。
"""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any

from loguru import logger

from pm_sports_bots.shared import RedisClient, TaskConfig

from .base import BaseRobot, StatusCallback


def _discover_robots() -> dict[str, type[BaseRobot]]:
    """自动扫描 *_bot/ 子目录，注册所有声明了 robot_type 的 BaseRobot 子类。"""
    robots_dir = Path(__file__).parent
    registry: dict[str, type[BaseRobot]] = {}

    for bot_dir in sorted(robots_dir.glob("*_bot")):
        if not bot_dir.is_dir() or not (bot_dir / "robot.py").exists():
            continue

        module_name = f"pm_sports_bots.robots.{bot_dir.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            logger.warning("自动发现：跳过 {} — {}", bot_dir.name, exc)
            continue

        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseRobot)
                and obj is not BaseRobot
                and getattr(obj, "robot_type", None)
            ):
                if obj.robot_type != bot_dir.name:
                    raise ValueError(
                        f"{bot_dir.name}/robot.py 中 robot_type='{obj.robot_type}' "
                        f"与目录名不一致，应改为 '{bot_dir.name}'"
                    )
                registry[obj.robot_type] = obj
                logger.debug("自动注册机器人: type={} class={}", obj.robot_type, obj.__name__)

    return registry


class TaskComposer:
    """根据 TaskConfig 创建并管理机器人。"""

    ROBOT_REGISTRY: dict[str, type[BaseRobot]] = _discover_robots()

    def __init__(self, redis: RedisClient):
        self.redis = redis
        self._robots: dict[str, list[BaseRobot]] = {}
        self._robot_tasks: dict[str, list[asyncio.Task[None]]] = {}

    @classmethod
    def available_robot_types(cls) -> list[str]:
        return sorted(cls.ROBOT_REGISTRY.keys())

    def compose(
        self,
        task_id: str,
        config: TaskConfig,
        status_callback: StatusCallback | None = None,
    ) -> list[BaseRobot]:
        """根据配置创建任务对应的机器人列表。

        未指定 custom_config.robots 时，默认启动 sample_producer + sample_consumer。
        """
        cfg = config.to_dict()
        custom_config = cfg.get("custom_config") or {}
        configured_robots = custom_config.get("robots")

        robots: list[BaseRobot] = []
        if configured_robots is None:
            for robot_type in ("ticker_bot", "transform_bot"):
                robot_cls = self.ROBOT_REGISTRY.get(robot_type)
                if robot_cls:
                    robots.append(robot_cls(task_id, self.redis, cfg, status_callback))
        else:
            if not isinstance(configured_robots, list):
                raise ValueError("custom_config.robots must be a list")

            for index, spec in enumerate(configured_robots):
                parsed = self._parse_robot_spec(spec, index)
                if parsed is None:
                    continue
                robot_type, robot_config = parsed
                robot_cls = self.ROBOT_REGISTRY.get(robot_type)
                if robot_cls is None:
                    available = ", ".join(self.available_robot_types())
                    raise ValueError(f"Unknown robot type: {robot_type}. Available: {available}")

                merged_config = dict(cfg)
                merged_config.update(robot_config)
                robots.append(robot_cls(task_id, self.redis, merged_config, status_callback))

            if not robots:
                raise ValueError("No robots are enabled for this task")

        self._robots[task_id] = robots
        logger.info("编排器已创建 {} 个机器人: task={}", len(robots), task_id)
        return robots

    def _parse_robot_spec(
        self,
        spec: Any,
        index: int,
    ) -> tuple[str, dict[str, Any]] | None:
        if isinstance(spec, str):
            return spec, {}

        if not isinstance(spec, dict):
            raise ValueError(f"Invalid robot spec at index {index}: must be string or object")

        if spec.get("enabled", True) is False:
            return None

        robot_type = spec.get("type")
        if not isinstance(robot_type, str) or not robot_type:
            raise ValueError(f"Invalid robot spec at index {index}: missing 'type'")

        robot_config = spec.get("config") or {}
        if not isinstance(robot_config, dict):
            raise ValueError(f"Invalid robot config for {robot_type}: must be object")

        return robot_type, robot_config

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
