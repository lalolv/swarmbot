"""示例轮询型机器人。

演示 Producer 模式：
- 无 input_streams，不消费任何信号
- 通过 tick_interval + on_tick() 周期性产生数据
- 使用 emit() 向 output_streams 发送信号
"""

from __future__ import annotations

import random
from datetime import datetime
from loguru import logger

from pm_sports_bots.shared.channels import SignalType, StreamName

from .base import BaseRobot


class SampleProducer(BaseRobot):
    """轮询型示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    每隔 tick_interval 秒执行一次 on_tick()，产生数据信号。
    """

    robot_type = "sample_producer"
    output_streams: list[StreamName] = [StreamName.DATA]  # 🔧 自定义点: 修改输出 stream

    @property
    def tick_interval(self) -> float:
        """轮询间隔（秒）。"""
        return float(self.config.get("poll_interval", 10.0))

    async def setup(self) -> None:
        """初始化资源。"""
        # 🔧 自定义点: 初始化外部连接、API 客户端等
        logger.info("SampleProducer 初始化完成: task={}", self.task_id)

    async def on_tick(self) -> None:
        """定时产生数据。"""
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
            "SampleProducer 已发送随机数信号: task={} value={}",
            self.task_id,
            data["value"],
        )
