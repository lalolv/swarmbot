<div align="center">

# Swarmbot

**Redis Streams · FastAPI · Vue 3 · 实时机器人编排**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)

[English](./README.md)

</div>

---

## 概览

Swarmbot 是一个自主机器人任务编排脚手架。每个任务由一组机器人组成，机器人通过 Redis Streams 互相通信，并通过 Server-Sent Events 将实时遥测数据推送至 Vue 3 仪表盘。

```
┌─────────────────┐   REST / SSE    ┌────────────────────────┐
│  Vue 3 前端:5173 │ ◄────────────── │  FastAPI 接口  :8000   │
│  无限画布        │ ──── CRUD ────► │  /api/v1/*             │
└─────────────────┘                 └───────────┬────────────┘
                                                │ Redis Stream: commands
                                    ┌───────────▼────────────┐
                                    │     TaskManager         │
                                    │   （消费组监听循环）     │
                                    └───────────┬────────────┘
                                                │ 派生
                                    ┌───────────▼────────────┐
                                    │       RobotTask         │
                                    │  ┌─────────┐ ┌───────┐ │
                                    │  │ ticker  │ │transf │ │
                                    │  └────┬────┘ └───┬───┘ │
                                    └───────┼──────────┼─────┘
                                            └────┬─────┘
                                    Redis Streams（每个任务独立）
                              swarmbot:task:{id}:stream:{name}
```

## 功能特性

- **可组合机器人** — 每个任务自由声明任意机器人组合；`TaskComposer` 自动发现 `*_bot/` 目录，无需手动注册
- **热更新** — PATCH 运行中任务的配置，机器人自动重启，任务不中断
- **休眠 / 唤醒** — 暂停任务（保留全部流数据），稍后恢复
- **崩溃恢复** — Worker 启动时自动扫描 Redis，恢复所有 `PENDING`/`RUNNING` 状态的任务
- **实时 SSE** — 双层流：全局任务投影 Feed + 单任务机器人遥测
- **无限画布 UI** — 支持平移/缩放的拓扑视图，显示机器人节点和实时流计数
- **Rust 机器人支持** — 继承 `RustRobotProxy`，Python 管理进程生命周期，Rust 二进制直接操作 Redis

## 环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.12 |
| [uv](https://github.com/astral-sh/uv) | 最新版 |
| Docker | 任意版本（本地 Redis） |
| Node.js | 18+ |

## 快速上手

```bash
# 1. 克隆并安装依赖
git clone <repo-url> && cd swarmbot
uv sync
cp .env.example .env

# 2. 启动 Redis
docker run --rm -p 6379:6379 redis:7

# 3. 启动 Worker（新终端）
uv run python -m swarmbot.worker.main

# 4. 启动 API（新终端）
uv run uvicorn swarmbot.api.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 启动前端（新终端）
cd frontend && npm install && npm run dev
```

打开 **http://localhost:5173** 访问仪表盘。Vite 开发服务器会将 `/api` 请求代理到 `:8000`。

## 接口参考

### 任务接口

```bash
# 创建任务（robots 字段必填）
curl -X POST http://localhost:8000/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "demo-1",
    "user_id": "u1",
    "robots": [
      {"type": "ticker_bot",    "config": {"poll_interval": 3.0, "min_value": 0, "max_value": 100}},
      {"type": "transform_bot", "config": {"multiplier": 1.5, "offset": 0.0}}
    ]
  }'

# 热更新运行中任务的配置
curl -X PATCH http://localhost:8000/api/v1/tasks/demo-1 \
  -H 'Content-Type: application/json' \
  -d '{"robots": [{"type": "ticker_bot", "config": {"poll_interval": 1.0}}]}'

# 休眠 / 唤醒
curl -X POST http://localhost:8000/api/v1/tasks/demo-1/sleep
curl -X POST http://localhost:8000/api/v1/tasks/demo-1/wake

# 删除并清除全部流数据
curl -X DELETE "http://localhost:8000/api/v1/tasks/demo-1?purge=true"
```

### SSE 流

| 端点 | 说明 |
|------|------|
| `GET /api/v1/live/tasks` | 全局任务投影 Feed（所有状态变更） |
| `GET /api/v1/live/subscribe/{task_id}` | 单任务机器人遥测流 |
| `GET /api/v1/live/subscribe/{task_id}?history=1` | 连接时包含近期历史数据 |

### 其他接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/tasks` | 列出所有任务 |
| `GET` | `/api/v1/tasks/{task_id}` | 获取任务状态 |
| `GET` | `/api/v1/robots` | 列出可用机器人类型 |

## 信号系统

每个机器人都可以同时**发出**信号和**接收**信号，通信完全通过限定在任务作用域内的 Redis Streams 进行。

### 流（Streams）

每个任务有三个内置流：

| 流 | 职责 | 默认生产者 | 默认消费者 |
|----|------|-----------|-----------|
| `data` | 原始数据 / 传感器读取 | 纯生产型机器人 | 变换型机器人 |
| `output` | 处理后的结果 | 变换型机器人 | 下游机器人、前端 |
| `control` | 系统生命周期事件 | `BaseRobot`（自动） | SSE 桥接、监控 |

控制流由框架自动写入，**不需要**在机器人代码中手动 emit。每个机器人启动、停止和出错时，都会自动向 `control` 流发送 `robot_start`、`robot_stop`、`robot_error` 信号。

### 信号字段

每条流消息对应一个 `Signal` 对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 信号类型，如 `data_update`、`process_result` |
| `source` | `str` | 发送方的 `robot_type` |
| `task_id` | `str` | 所属任务 ID |
| `timestamp` | `str` | ISO 8601 UTC 时间戳 |
| `data` | `dict` | 业务数据（任意 JSON 结构） |
| `schema_version` | `str` | `"1.0"` — 生产者和消费者必须保持一致 |
| `id` | `str` | Redis Stream 消息 ID（读取时自动填充） |

### 两种机器人原型

**纯生产型（Pure Producer）** — 自驱动生成数据，不订阅任何流：

```
ticker_bot
  setup() → asyncio.create_task(_tick_loop())
  _tick_loop():
    while not cancelled:
      emit(DATA, DATA_UPDATE, {"value": 42.0, ...})  ──► data 流
      sleep(poll_interval)
```

```python
class TickerBot(BaseRobot):
    robot_type = "ticker_bot"
    input_streams  = []                  # 不订阅任何流
    output_streams = [StreamName.DATA]

    async def setup(self) -> None:
        self._tick = asyncio.create_task(self._tick_loop())

    async def teardown(self) -> None:
        self._tick.cancel()
        await asyncio.gather(self._tick, return_exceptions=True)

    async def _tick_loop(self) -> None:
        while not self._cancelled:
            await self.emit(StreamName.DATA, SignalType.DATA_UPDATE, {"value": ...})
            await asyncio.sleep(float(self.robot_config.get("poll_interval", 5.0)))
```

**变换型（Transformer）** — 响应输入信号，生成派生结果：

```
transform_bot
  run_loop() xread(data 流) ──► on_signal()
    signal.type == DATA_UPDATE:
      emit(OUTPUT, PROCESS_RESULT, {"result": ...})  ──► output 流
```

```python
class TransformBot(BaseRobot):
    robot_type = "transform_bot"
    input_streams  = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]

    async def setup(self) -> None:
        pass  # 无状态，run_loop 驱动一切

    async def on_signal(self, stream: str, signal: Signal) -> None:
        if signal.type == SignalType.DATA_UPDATE:
            value = float(signal.data["value"])
            result = value * float(self.robot_config.get("multiplier", 1.5))
            await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, {"result": result})
        # 未知类型静默忽略
```

### 演示信号流

```
ticker_bot                             transform_bot
    │                                       │
    │ emit(DATA, data_update)               │
    └──────── data 流 ──────────────────────►│ on_signal("data", signal)
                                            │
                                            │ emit(OUTPUT, process_result)
                                            └──── output 流 ──────────────► SSE 桥接 ──► 前端
                                                                                   (process_result 事件)
两个机器人都会自动写入控制流：
    robot_start / robot_stop / robot_error  ──► control 流 ──► 前端（robot_status 事件）
```

### SSE 事件类型

SSE 桥接将 Redis Stream 信号映射为前端事件：

| SSE 事件 | 来源信号 | 关键载荷字段 |
|----------|---------|------------|
| `data_update` | `data_update` 信号 | `robot_type`、`task_id`、`data {}` |
| `process_result` | `process_result` 信号 | `robot_type`、`task_id`、`data {}` |
| `robot_status` | `robot_start` / `robot_stop` / `robot_error` | `robot_type`、`state`、`last_error` |
| `task_status` | `task_status` 信号 | 完整 `TaskStatus` JSON |
| `task_end` | Redis 状态键轮询（非 Stream） | `task_id`、`state` |
| `heartbeat` | 当前轮询无新消息 | `ts` |

> **注意：** `task_end` 不从流日志转发，而是由桥接轮询 Redis 状态键合成。这样可以避免休眠/唤醒后重连时重放过期的终态信号。

### 添加自定义信号类型

1. 在 `swarmbot/shared/channels.py` 的 `SignalType` 中添加枚举值
2. 在 `swarmbot/api/routes/live_stream.py` 的 `_signal_to_sse()` 中添加映射
3. 在接收方机器人的 `on_signal()` 中处理 `signal.type == "your_type"`

### 状态广播与运行指标

每次 `emit()` 调用和每次接收到信号后，机器人都会向前端推送一次状态快照。覆盖 `get_runtime_metrics()` 可将自定义计数器并入该快照：

```python
def get_runtime_metrics(self) -> dict[str, Any]:
    return {"processed": self._count, "last_value": self._last}
```

对于高频机器人（如每秒处理数千个信号的量化交易机器人），设置 `status_broadcast_min_interval = 2.0` 可节流状态推送，而不影响信号处理管线的速度。

## 添加机器人

在 `swarmbot/robots/my_bot/` 下创建 `__init__.py` 和 `robot.py`，`TaskComposer` 会自动发现它，无需任何注册：

```python
# swarmbot/robots/my_bot/robot.py
class MyBot(BaseRobot):
    robot_type = "my_bot"                        # 必须与目录名一致
    input_streams  = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
    status_broadcast_min_interval = 2.0          # 高频机器人可设置节流间隔

    async def setup(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def teardown(self) -> None:
        self._task.cancel()
        await asyncio.gather(self._task, return_exceptions=True)

    async def on_signal(self, stream: str, signal: Signal) -> None:
        if signal.type == SignalType.DATA_UPDATE:
            await self.emit(StreamName.OUTPUT, SignalType.PROCESS_RESULT, {"result": ...})
        # 未知信号类型静默忽略

    def get_runtime_metrics(self) -> dict[str, Any]:
        return {"my_counter": self._counter}     # 会在前端状态面板中展示
```

然后在任务中声明：
```json
{"robots": [{"type": "my_bot", "config": {"key": "value"}}]}
```

## 开发

```bash
# 语法检查（每次提交前的最低要求）
uv run python -m compileall swarmbot scripts

# 代码检查与格式化
uv run ruff check --fix swarmbot scripts
uv run ruff format swarmbot scripts

# 测试（当前暂无测试目录，以下为参考命令）
uv run pytest
uv run pytest tests/test_file.py::test_name -q
uv run pytest -x

# 通过脚本提交演示任务
uv run python scripts/publish_demo_task.py
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `EXECUTION_DEDUPE_TTL_SECONDS` | `300` | 防止重复启动任务的去重 TTL（秒） |
