"""示例机器人：定期生成随机价格数据。

无 input_streams，在 setup() 中用 asyncio.create_task() 启动轮询循环，
周期性向 data stream 发送随机数信号。
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime

from loguru import logger

from pm_sports_bots.robots.base import BaseRobot
from pm_sports_bots.shared.channels import SignalType, StreamName


class TickerBot(BaseRobot):
    """定期生成随机价格数据的示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    在 setup() 中启动 _tick_loop，按 poll_interval 周期性产生数据信号。
    """

    robot_type = "ticker_bot"
    output_streams: list[StreamName] = [StreamName.DATA]  # 🔧 自定义点: 修改输出 stream

    async def setup(self) -> None:
        """初始化资源，启动数据产生循环。"""
        # 🔧 自定义点: 初始化外部连接、API 客户端等
        logger.info("TickerBot 初始化完成: task={}", self.task_id)
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def teardown(self) -> None:
        """取消数据产生循环。"""
        self._tick_task.cancel()
        await asyncio.gather(self._tick_task, return_exceptions=True)

    async def _tick_loop(self) -> None:
        """周期性产生随机价格信号。"""
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
                "TickerBot 已发送随机数信号: task={} value={}",
                self.task_id,
                data["value"],
            )
            await asyncio.sleep(interval)
