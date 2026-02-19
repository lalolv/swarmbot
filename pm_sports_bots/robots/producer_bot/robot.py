"""示例轮询型机器人 (Producer)。

演示 Producer 模式：
- 无 input_streams，不消费任何信号
- 在 setup() 中用 asyncio.create_task() 启动自己的轮询循环
- 使用 emit() 向 output_streams 发送信号
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime

from loguru import logger

from pm_sports_bots.robots.base import BaseRobot
from pm_sports_bots.shared.channels import SignalType, StreamName


class ProducerBot(BaseRobot):
    """轮询型示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    在 setup() 中启动 _produce_loop，按 poll_interval 周期性产生数据信号。
    """

    robot_type = "producer_bot"
    output_streams: list[StreamName] = [StreamName.DATA]  # 🔧 自定义点: 修改输出 stream

    async def setup(self) -> None:
        """初始化资源，启动数据产生循环。"""
        # 🔧 自定义点: 初始化外部连接、API 客户端等
        logger.info("ProducerBot 初始化完成: task={}", self.task_id)
        self._produce_task = asyncio.create_task(self._produce_loop())

    async def teardown(self) -> None:
        """取消数据产生循环。"""
        self._produce_task.cancel()
        await asyncio.gather(self._produce_task, return_exceptions=True)

    async def _produce_loop(self) -> None:
        """周期性产生随机数数据信号。"""
        while not self._cancelled:
            interval = float(self.config.get("poll_interval", 10.0))
            min_value = float(self.config.get("min_value", 0.0))
            max_value = float(self.config.get("max_value", 100.0))
            random_value = random.uniform(min_value, max_value)

            data = {
                "value": round(random_value, 4),
                "min_value": min_value,
                "max_value": max_value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            await self.emit(StreamName.DATA, SignalType.DATA_UPDATE, data)
            logger.debug(
                "ProducerBot 已发送随机数信号: task={} value={}",
                self.task_id,
                data["value"],
            )
            await asyncio.sleep(interval)
