"""Rust 量化交易机器人 Python 代理。

实际算法在 src/main.rs 中实现，享有 Rust 的完整性能
（tokio 异步、无 GIL、零成本抽象）。
"""

from __future__ import annotations

import os

from pm_sports_bots.robots.rust_proxy import RustRobotProxy
from pm_sports_bots.shared.channels import StreamName

_BIN = os.path.join(os.path.dirname(__file__), "target/release/trading-bot")


class TradingBot(RustRobotProxy):
    """Rust 量化交易机器人代理。"""

    robot_type = "trading_bot"
    rust_binary = os.path.abspath(_BIN)

    input_streams = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]

    # 降低 Python 侧状态广播频率，减少开销
    status_broadcast_min_interval = 5.0
