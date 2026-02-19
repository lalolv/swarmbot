"""示例机器人：对输入数据做线性变换。

声明 input_streams，实现 on_signal() 响应外部信号，
对接收到的数值做线性变换后写入 output 流。
"""

from __future__ import annotations

from loguru import logger

from pm_sports_bots.robots.base import BaseRobot, Signal
from pm_sports_bots.shared.channels import SignalType, StreamName


class TransformBot(BaseRobot):
    """对输入数据做线性变换的示例机器人。

    # 🔧 自定义点: 修改为你的业务逻辑
    订阅 data stream，接收并处理数据信号，生成输出信号。
    """

    robot_type = "transform_bot"
    input_streams: list[StreamName] = [StreamName.DATA]     # 🔧 自定义点: 修改订阅的 stream
    output_streams: list[StreamName] = [StreamName.OUTPUT]  # 🔧 自定义点: 修改输出 stream

    async def setup(self) -> None:
        """初始化资源。"""
        # 🔧 自定义点: 初始化处理所需的状态、模型等
        logger.info("TransformBot 初始化完成: task={}", self.task_id)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        """处理输入信号。

        根据 signal.type 路由到不同的处理方法。
        """
        # 🔧 自定义点: 添加你的信号类型处理逻辑
        if signal.type == SignalType.DATA_UPDATE:
            await self._handle_data_update(signal)
        else:
            logger.debug(
                "TransformBot 跳过未知信号: type={} stream={}",
                signal.type,
                stream,
            )

    async def _handle_data_update(self, signal: Signal) -> None:
        """处理数据更新信号。"""
        input_data = signal.data
        raw_value = input_data.get("value")
        if raw_value is None:
            logger.debug("TransformBot 收到无 value 的信号: task={}", self.task_id)
            return

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            logger.warning(
                "TransformBot 信号 value 非数字: task={} value={}",
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
        await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, result)
        logger.debug(
            "TransformBot 已处理数值: task={} input={} result={}",
            self.task_id,
            value,
            transformed,
        )
