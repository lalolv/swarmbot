"""Rust 子进程机器人代理基类。

Rust 机器人以独立进程运行，直接通过 Redis Streams 与系统通信，
无需经过 Python 中间层。Python 侧仅负责生命周期管理（启动/监控/停止）。

通信契约（Rust 进程必须遵守）：
  - 从环境变量读取：TASK_ID、REDIS_URL、INPUT_STREAMS、OUTPUT_STREAMS
  - Stream Key 格式：pm_sports_bots:task:{TASK_ID}:stream:{stream_name}
  - Signal 字段：type、source、task_id、timestamp、schema_version、data（JSON 字符串）
  - 启动时向 control stream 写入 robot_start 信号
  - 收到 SIGTERM 时优雅关闭，写入 robot_stop 信号

用法示例：
    class TradingBot(RustRobotProxy):
        robot_type = "trading_bot"
        rust_binary = "/path/to/trading-bot"         # 编译好的 Rust 可执行文件
        input_streams = [StreamName.DATA]
        output_streams = [StreamName.OUTPUT]
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from pm_sports_bots.robots.base import BaseRobot, RobotState, RobotStatus, StatusCallback, _now_iso
from pm_sports_bots.shared import RedisClient
from pm_sports_bots.shared.channels import Channels, StreamName


class RustRobotProxy(BaseRobot):
    """Rust 子进程机器人代理基类。

    子类只需声明 robot_type、rust_binary 以及 input/output_streams，
    Rust 进程会直接连接 Redis 并处理所有信号，Python 侧不重复消费流。
    """

    rust_binary: str = ""
    """Rust 可执行文件路径（子类必须声明绝对路径）。"""

    def __init__(
        self,
        task_id: str,
        redis: RedisClient,
        config: dict[str, Any] | None = None,
        status_callback: StatusCallback | None = None,
    ):
        super().__init__(task_id, redis, config, status_callback)
        self._process: asyncio.subprocess.Process | None = None
        self._monitor_task: asyncio.Task | None = None
        self._sync_task: asyncio.Task | None = None
        # Rust 侧的真实计数，由 _sync_rust_counts 后台任务从 control stream 同步
        self._rust_signals_in: int = 0
        self._rust_signals_out: int = 0

    async def start(self) -> None:
        """覆盖父类：跳过 Python 侧的 robot_start emit。

        Rust 进程启动后自己向 control stream 写 robot_start，Python 不重复写。
        """
        self._cancelled = False
        self._state = RobotState.RUNNING
        self._started_at = _now_iso()
        try:
            await self.setup()
            await self._broadcast_status()
        except Exception as exc:
            self._state = RobotState.ERROR
            self._last_error = str(exc)
            logger.error("Rust Robot {} setup 失败: {}", self.robot_type, exc)
            await self._broadcast_status()
            raise

    async def stop(self) -> None:
        """覆盖父类：跳过 Python 侧的 robot_stop emit。

        Rust 进程收到 SIGTERM 后自己向 control stream 写 robot_stop。
        """
        self._cancelled = True
        try:
            await self.teardown()
        except Exception as exc:
            logger.warning("Rust Robot {} teardown 异常: {}", self.robot_type, exc)
        self._state = RobotState.STOPPED
        await self._broadcast_status()
        logger.info("Rust Robot 已停止: type={} task={}", self.robot_type, self.task_id)

    async def setup(self) -> None:
        """启动 Rust 子进程，通过环境变量传递上下文。"""
        if not self.rust_binary:
            raise ValueError(
                f"{self.__class__.__name__} 未声明 rust_binary，"
                "请在子类中设置 rust_binary = '/path/to/binary'"
            )

        if not os.path.isfile(self.rust_binary):
            cargo_dir = Path(self.rust_binary).parent.parent.parent
            raise FileNotFoundError(
                f"Rust 二进制不存在: {self.rust_binary}\n"
                f"请先编译: cd {cargo_dir} && cargo build --release"
            )

        # 将简单类型的 config 字段展开为 BOT_* 环境变量
        bot_env = {
            f"BOT_{k.upper()}": str(v)
            for k, v in self.config.items()
            if isinstance(v, (str, int, float, bool))
        }

        env = {
            **os.environ,
            "TASK_ID": self.task_id,
            "REDIS_URL": self.redis._url,
            "ROBOT_TYPE": self.robot_type,
            "INPUT_STREAMS": ",".join(s.value for s in self.input_streams),
            "OUTPUT_STREAMS": ",".join(s.value for s in self.output_streams),
            **bot_env,
        }

        self._process = await asyncio.create_subprocess_exec(
            self.rust_binary,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info(
            "Rust 机器人已启动: type={} pid={} binary={}",
            self.robot_type,
            self._process.pid,
            self.rust_binary,
        )

        self._monitor_task = asyncio.create_task(
            self._monitor_process(),
            name=f"rust-monitor:{self.task_id}:{self.robot_type}",
        )
        self._sync_task = asyncio.create_task(
            self._sync_rust_counts(),
            name=f"rust-sync:{self.task_id}:{self.robot_type}",
        )

    async def teardown(self) -> None:
        """终止 Rust 子进程，先 SIGTERM 优雅关闭，超时后 SIGKILL。"""
        for task in (self._sync_task, self._monitor_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(
                    "Rust 进程未响应 SIGTERM，强制 SIGKILL: type={} pid={}",
                    self.robot_type,
                    self._process.pid,
                )
                self._process.kill()
                await self._process.wait()

        if self._process:
            logger.info(
                "Rust 机器人已停止: type={} pid={} code={}",
                self.robot_type,
                self._process.pid,
                self._process.returncode,
            )

    async def run_loop(self) -> None:
        """覆盖父类：Rust 进程直接操作 Redis，Python 侧只监控进程健康。"""
        if self._state != RobotState.RUNNING:
            await self.start()

        try:
            while not self._cancelled:
                # 检测 Rust 进程是否已退出
                if self._process and self._process.returncode is not None:
                    code = self._process.returncode
                    if code != 0 and not self._cancelled:
                        raise RuntimeError(
                            f"Rust 进程异常退出: code={code}"
                        )
                    break
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._state = RobotState.ERROR
            self._last_error = str(exc)
            logger.error(
                "Rust 机器人代理异常: type={} err={}",
                self.robot_type,
                exc,
            )
        finally:
            await self.stop()

    async def _monitor_process(self) -> None:
        """将 Rust 进程的 stdout/stderr 转发到 loguru，并检测异常退出。"""
        if not self._process:
            return

        async def _pipe_stdout(stream: asyncio.StreamReader) -> None:
            async for line in stream:
                logger.debug(
                    "[Rust:{}] {}",
                    self.robot_type,
                    line.decode(errors="replace").rstrip(),
                )

        async def _pipe_stderr(stream: asyncio.StreamReader) -> None:
            async for line in stream:
                text = line.decode(errors="replace").rstrip()
                # tracing-subscriber 格式: "2026-...Z  INFO msg" / " WARN " / "ERROR " / "DEBUG "
                upper = text.upper()
                if " ERROR " in upper:
                    logger.error("[Rust:{}] {}", self.robot_type, text)
                elif " WARN " in upper:
                    logger.warning("[Rust:{}] {}", self.robot_type, text)
                elif " DEBUG " in upper:
                    logger.debug("[Rust:{}] {}", self.robot_type, text)
                else:
                    logger.info("[Rust:{}] {}", self.robot_type, text)

        pipe_tasks: list[asyncio.Task] = []
        if self._process.stdout:
            pipe_tasks.append(asyncio.create_task(_pipe_stdout(self._process.stdout)))
        if self._process.stderr:
            pipe_tasks.append(asyncio.create_task(_pipe_stderr(self._process.stderr)))

        returncode = await self._process.wait()

        for t in pipe_tasks:
            t.cancel()
        if pipe_tasks:
            await asyncio.gather(*pipe_tasks, return_exceptions=True)

        if returncode != 0 and not self._cancelled:
            logger.error(
                "Rust 进程异常退出: type={} pid={} code={}",
                self.robot_type,
                self._process.pid,
                returncode,
            )
            self._last_error = f"Rust process exited with code {returncode}"

    async def _sync_rust_counts(self) -> None:
        """从 control stream 轮询 Rust 侧发出的 robot_status，同步真实信号计数。

        Rust 进程每处理 N 个信号就向 control stream 写入一条 robot_status，
        此任务读取这些消息并更新 _rust_signals_in / _rust_signals_out，
        使 get_status() 返回有意义的计数而非 Python proxy 的 0/1。
        """
        control_stream = Channels.task_stream(self.task_id, Channels.STREAM_CONTROL)
        last_id = "0"  # 从头读，避免错过 Rust 已发出的第一批状态

        while not self._cancelled:
            try:
                results = await self.redis.xread(
                    streams={control_stream: last_id},
                    count=50,
                    block=None,  # 非阻塞，立即返回
                )
                for _, messages in results:
                    for msg_id, fields in messages:
                        last_id = msg_id
                        if (
                            fields.get("source") == self.robot_type
                            and fields.get("type") == "robot_status"
                        ):
                            try:
                                data = json.loads(fields.get("data", "{}"))
                                self._rust_signals_in = int(data.get("signals_in", self._rust_signals_in))
                                self._rust_signals_out = int(data.get("signals_out", self._rust_signals_out))
                            except Exception:
                                pass
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("rust_proxy 同步计数失败: {}", exc)

            await asyncio.sleep(5.0)

    def get_status(self) -> RobotStatus:
        """覆盖父类：用 Rust 侧同步到的真实计数替换 Python proxy 的 0/1。"""
        status = super().get_status()
        status.signals_in = self._rust_signals_in
        status.signals_out = self._rust_signals_out
        return status
