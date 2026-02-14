"""示例轮询型机器人。

演示 Producer 模式：
- 无 input_streams，不消费任何信号
- 通过 tick_interval + on_tick() 周期性产生数据
- 使用 emit() 向 output_streams 发送信号
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from .base import BaseRobot, Signal


class SampleProducer(BaseRobot):
    """轮询型示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    每隔 tick_interval 秒执行一次 on_tick()，产生数据信号。
    """

    robot_type = "sample_producer"
    input_streams: list[str] = []        # 轮询型无输入
    output_streams: list[str] = ["data"] # 🔧 自定义点: 修改输出 stream

    @property
    def tick_interval(self) -> float:
        """轮询间隔（秒）。"""
        return float(self.config.get("poll_interval", 10.0))

    async def setup(self) -> None:
        """初始化资源。"""
        # 🔧 自定义点: 初始化外部连接、API 客户端等
        logger.info("SampleProducer 初始化完成: task={}", self.task_id)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        """轮询型机器人不处理输入信号。"""
        return

    async def on_tick(self) -> None:
        """定时产生数据。"""
        # 🔧 自定义点: 替换为实际的数据获取逻辑
        data = {
            "message": "示例数据",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        await self.emit("data", "data_update", data)
        logger.debug("SampleProducer 已发送数据信号: task={}", self.task_id)
