# Python 信号驱动型机器人模板

声明 input_streams，实现 `on_signal()` 响应外部信号，可选地发出新信号。

## robot.py

```python
"""{描述}"""

from __future__ import annotations

from loguru import logger

from swarmbot.robots.base import BaseRobot, Signal
from swarmbot.shared.channels import SignalType, StreamName


class {ClassName}(BaseRobot):
    """{描述}"""

    robot_type = "{name}_bot"                           # 必须与目录名完全一致
    input_streams: list[StreamName] = [StreamName.{INPUT_STREAM}]
    output_streams: list[StreamName] = [StreamName.{OUTPUT_STREAM}]

    async def setup(self) -> None:
        # 🔧 自定义点: 初始化处理所需的状态、模型、外部连接等
        logger.info("{ClassName} 初始化完成: task={}", self.task_id)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        """根据信号类型路由处理。"""
        if signal.type == SignalType.DATA_UPDATE:
            await self._handle_data_update(signal)
        else:
            logger.debug(
                "{ClassName} 跳过未知信号: type={} stream={}",
                signal.type,
                stream,
            )

    async def _handle_data_update(self, signal: Signal) -> None:
        """处理数据更新信号。"""
        data = signal.data
        value = data.get("value")
        if value is None:
            return

        # 🔧 自定义点: 替换为实际处理逻辑
        result = {
            "input_value": value,
            "result_value": float(value) * 1.0,
            "timestamp": signal.timestamp,
        }

        await self.emit(StreamName.{OUTPUT_STREAM}, SignalType.PROCESS_RESULT, result)
        logger.debug("{ClassName} 已处理信号: task={}", self.task_id)
```

## __init__.py

```python
from .robot import {ClassName}

__all__ = ["{ClassName}"]
```

## 配置参数（通过 config 字典传入）

根据业务需要添加，例如：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `multiplier` | float | 1.0 | 处理系数 |

## 注意事项

- `xread_block_ms = 100` 可降低延迟（默认 1000ms），适合低延迟场景
- `on_signal()` 抛出的异常由 `run_loop()` 捕获并记录，不会中断循环
- 多个信号类型分别路由到独立的 `_handle_*` 方法，保持 `on_signal()` 清晰
