"""示例响应型机器人。

演示 Consumer 模式：
- 订阅 input_streams，在 on_signal() 中路由处理不同信号类型
- 消费输入信号 → 处理 → 可选地发出新信号
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .base import BaseRobot, Signal


class SampleConsumer(BaseRobot):
    """响应型示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    订阅 data stream，接收并处理数据信号，生成输出信号。
    """

    robot_type = "sample_consumer"
    input_streams: list[str] = ["data"]      # 🔧 自定义点: 修改订阅的 stream
    output_streams: list[str] = ["output"]   # 🔧 自定义点: 修改输出 stream

    async def setup(self) -> None:
        """初始化资源。"""
        # 🔧 自定义点: 初始化处理所需的状态、模型等
        logger.info("SampleConsumer 初始化完成: task={}", self.task_id)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        """处理输入信号。

        根据 signal.type 路由到不同的处理方法。
        """
        # 🔧 自定义点: 添加你的信号类型处理逻辑
        if signal.type == "data_update":
            await self._handle_data_update(signal)
        else:
            logger.debug(
                "SampleConsumer 跳过未知信号: type={} stream={}",
                signal.type,
                stream,
            )

    async def _handle_data_update(self, signal: Signal) -> None:
        """处理数据更新信号。"""
        input_data = signal.data
        raw_value = input_data.get("value")
        if raw_value is None:
            logger.debug("SampleConsumer 收到无 value 的信号: task={}", self.task_id)
            return

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            logger.warning(
                "SampleConsumer 信号 value 非数字: task={} value={}",
                self.task_id,
                raw_value,
            )
            return

        coefficient = float(self.config.get("multiplier", 1.5))
        offset = float(self.config.get("offset", 0.0))
        transformed = round(value * coefficient + offset, 4)

        result = {
            "source_type": signal.type,
            "input_value": value,
            "coefficient": coefficient,
            "offset": offset,
            "result_value": transformed,
            "timestamp": signal.timestamp,
        }
        await self.emit("output", "process_result", result)
        logger.debug(
            "SampleConsumer 已处理随机数: task={} input={} result={}",
            self.task_id,
            value,
            transformed,
        )
