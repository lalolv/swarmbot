# Python 自驱型机器人模板

无 input_streams，在 `setup()` 中用 `asyncio.create_task()` 启动循环，自行产生数据。

## robot.py

```python
"""{描述}"""

from __future__ import annotations

import asyncio

from loguru import logger

from swarmbot.robots.base import BaseRobot
from swarmbot.shared.channels import SignalType, StreamName


class {ClassName}(BaseRobot):
    """{描述}"""

    robot_type = "{name}_bot"                          # 必须与目录名完全一致
    output_streams: list[StreamName] = [StreamName.{OUTPUT_STREAM}]

    async def setup(self) -> None:
        logger.info("{ClassName} 初始化完成: task={}", self.task_id)
        self._loop_task = asyncio.create_task(self._run_loop())

    async def teardown(self) -> None:
        self._loop_task.cancel()
        await asyncio.gather(self._loop_task, return_exceptions=True)

    async def _run_loop(self) -> None:
        while not self._cancelled:
            interval = float(self.config.get("poll_interval", 5.0))

            # 🔧 自定义点: 替换为实际的数据获取逻辑
            data = {
                "value": 0.0,
                # ...
            }

            await self.emit(StreamName.{OUTPUT_STREAM}, SignalType.DATA_UPDATE, data)
            logger.debug("{ClassName} 已发送信号: task={}", self.task_id)
            await asyncio.sleep(interval)
```

## __init__.py

```python
from .robot import {ClassName}

__all__ = ["{ClassName}"]
```

## 配置参数（通过 config 字典传入）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `poll_interval` | float | 5.0 | 轮询间隔（秒） |

## 注意事项

- `teardown()` 必须取消并 await `_loop_task`，否则任务停止时协程泄漏
- 使用 `self._cancelled` 判断是否退出，不要用全局标志
- 高频发送可设置 `status_broadcast_min_interval = 2.0` 降低状态广播开销
