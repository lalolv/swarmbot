

# Swarmbot

**面向 Agentic Bot 与 Prefab Bot 的任务驱动蜂群编排系统**

[Python](https://www.python.org/)
[FastAPI](https://fastapi.tiangolo.com/)
[Vue](https://vuejs.org/)
[Redis](https://redis.io/)

*组合机器人蜂群，让信号自由流动，看任务自然涌现。*

[English](./README.md)



---

## 为什么选择 Swarmbot？

我们相信未来是**任务驱动**的 —— 复杂的工作将被分解为一个个任务，每个任务由一群专业化的机器人通过信号协作完成。

Swarmbot 正是为此而生的运行时：你声明一个任务，组建一支机器人团队，系统负责编排、通信和实时可观测。

### 核心设计理念

**1. 任务是一等公民**

一切始于任务。任务不只是一个待运行的作业 —— 它是一个自包含的工作单元，拥有自己的机器人团队、通信通道和生命周期。创建、热更新、休眠、唤醒、销毁 —— 任务是唯一的控制入口。

**2. 蜂群协作优于单体智能**

不是一个大型 Agent 包办一切，而是将工作分散到一群专注的机器人上。每个机器人做好一件事，通过 Redis Streams 上的信号与其他机器人通信。这种「蜂巢思维」架构天然支持扩展 —— 向任务中添加更多机器人，无需修改已有的。

**3. 确定性与创造性共存**

每个真实的任务都同时包含确定性工作和创造性工作。确定性代码 —— 如 `1 + 1 = 2` —— 保障系统的**可靠性**：数据采集、数学变换、格式转换，永远产生相同的结果。创造性代码 —— 由 AI 驱动 —— 保障系统的**创新性**：每次运行可能生成不同的洞察、内容或策略。

Swarmbot 拥抱这种二元性。同一个通用的 `BaseRobot` 接口既可以承载确定性的轮询机器人，也可以承载 LLM 驱动的分析机器人。你选择每个机器人的逻辑本质；框架一视同仁地对待它们。

**4. 信号是通用语言**

机器人之间永不直接调用。所有通信通过任务作用域内的 Redis Streams 上的类型化信号流动。这种解耦意味着机器人可以随时添加、移除或替换，而不影响蜂群的其他部分。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              任务 (Task)                                │
│                                                                         │
│  ┌───────────┐                             ┌───────────┐                │
│  │ ticker_bot│── data 流 ────────────────►│ analyst_bot│                │
│  │ (数据轮询) │   {value: 42.0}            │ (LLM 分析) │                │
│  └───────────┘                             └─────┬─────┘                │
│                                                   │                     │
│  ┌────────────┐◄── output 流 ────────────────────┘                     │
│  │transform_bot│   {insight: "..."}                                     │
│  │ (格式转换)   │                                                        │
│  └─────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## 目录

- [功能特性](#功能特性)
- [架构](#架构)
- [快速上手](#快速上手)
- [接口参考](#接口参考)
- [信号系统](#信号系统)
- [机器人开发](#机器人开发)
- [开发](#开发)
- [环境变量](#环境变量)

## 功能特性

- **可组合机器人蜂群** — 每个任务自由声明任意机器人组合；`TaskComposer` 自动发现 `*_bot/` 目录，无需手动注册
- **热更新** — PATCH 运行中任务的配置，机器人自动停止并以新配置重启，任务零停机
- **休眠 / 唤醒** — 暂停任务（保留全部流数据），稍后恢复
- **崩溃恢复** — Worker 启动时自动扫描 Redis，恢复所有 `PENDING`/`RUNNING` 状态的任务
- **实时 SSE** — 双层流：全局任务投影 + 单任务机器人遥测
- **无限画布 UI** — 支持平移/缩放的拓扑视图，实时显示机器人节点和流计数
- **多语言机器人** — 支持 Python 和 Rust 编写机器人；`RustRobotProxy` 管理 Rust 子进程生命周期，二进制直接操作 Redis

## 架构

```
┌─────────────────┐   REST / SSE    ┌────────────────────────┐
│  Vue 3 前端:5173 │ ◄────────────── │  FastAPI 接口  :8000   │
│  无限画布        │ ──── CRUD ────► │  /api/v1/*             │
└─────────────────┘                 └───────────┬────────────┘
                                                │ Redis Stream: commands
                                    ┌───────────▼────────────┐
                                    │      TaskManager        │
                                    │   （消费组监听循环）     │
                                    └───────────┬────────────┘
                                                │ 派生
                                    ┌───────────▼────────────┐
                                    │       RobotTask         │
                                    │  ┌─────────┐ ┌───────┐ │
                                    │  │ bot A  │ │ bot B │ │
                                    │  └────┬────┘ └───┬───┘ │
                                    └───────┼──────────┼─────┘
                                            └────┬─────┘
                                    Redis Streams（每个任务独立）
                              swarmbot:task:{id}:stream:{name}
```

### 项目结构

```
swarmbot/
├── shared/       # Redis 客户端、通道/键命名、领域模型、Schema
├── robots/       # BaseRobot 抽象类、RustRobotProxy、TaskComposer、机器人实现
│   ├── ticker_bot/       # 示例：自驱动数据生产者
│   ├── transform_bot/    # 示例：信号驱动变换器
│   └── trading_bot/      # 示例：基于 Rust 的机器人
├── worker/       # TaskManager、RobotTask、ExecutionDedupe
└── api/          # FastAPI 路由、SSE 桥接

frontend/src/
├── components/   # Vue 3 组件（画布、面板、卡片）
├── stores/       # Pinia 状态管理（可观测性、主题）
├── api/          # HTTP 客户端与 SSE 订阅
└── themes/       # 多主题设计系统
```

### 任务生命周期

```
   创建 ──► PENDING ──► RUNNING ──► COMPLETED
                │             │
                │         休眠/唤醒
                │             │
                ▼             ▼
            CANCELLED     SLEEPING ──► RUNNING
                              │
                              ▼
                           FAILED
```

1. API 发布 `create` 命令到 `swarmbot:stream:commands`
2. Worker 的 `TaskManager` 通过消费组消费命令，启动 `RobotTask.run()`
3. `TaskComposer.compose()` 实例化声明的机器人蜂群
4. 机器人向任务作用域的流发送信号 (`swarmbot:task:{id}:stream:{name}`)
5. SSE 桥接将事件实时推送至前端
6. PATCH 触发热更新；DELETE 取消并清除数据

## 快速上手

### 环境要求


| 工具                                    | 版本             |
| ------------------------------------- | -------------- |
| Python                                | 3.12           |
| [uv](https://github.com/astral-sh/uv) | 最新版            |
| Docker                                | 任意版本（本地 Redis） |
| Node.js                               | 18+            |


### 启动

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

打开 **[http://localhost:5173](http://localhost:5173)** 访问仪表盘。Vite 开发服务器会将 `/api` 请求代理到 `:8000`。

## 接口参考

### 任务操作

```bash
# 创建任务，组建机器人蜂群
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

### 全部端点


| 方法       | 路径                                 | 说明           |
| -------- | ---------------------------------- | ------------ |
| `GET`    | `/api/v1/tasks`                    | 列出所有任务       |
| `POST`   | `/api/v1/tasks`                    | 创建任务（发布命令）   |
| `GET`    | `/api/v1/tasks/{task_id}`          | 获取任务状态       |
| `PATCH`  | `/api/v1/tasks/{task_id}`          | 更新配置（触发热更新）  |
| `DELETE` | `/api/v1/tasks/{task_id}`          | 取消并清除任务      |
| `POST`   | `/api/v1/tasks/{task_id}/sleep`    | 休眠任务         |
| `POST`   | `/api/v1/tasks/{task_id}/wake`     | 唤醒任务         |
| `GET`    | `/api/v1/live/tasks`               | SSE：全局任务投影   |
| `GET`    | `/api/v1/live/subscribe/{task_id}` | SSE：单任务机器人遥测 |
| `GET`    | `/api/v1/robots`                   | 列出可用机器人类型    |


> 在单任务 SSE 端点后追加 `?history=1` 可在连接时包含近期历史数据。

## 信号系统

机器人之间通过**信号**通信 —— 任务作用域 Redis Streams 上的类型化消息。机器人永不直接调用另一个机器人；它发出信号，订阅了该流的机器人自动响应。

### 流（Streams）

每个任务有三个内置流：


| 流         | 职责           | 说明                             |
| --------- | ------------ | ------------------------------ |
| `data`    | 原始数据 / 传感器读取 | 生成数据的机器人向此写入；需要原始输入的机器人从此读取    |
| `output`  | 处理后的结果       | 变换或分析数据的机器人向此写入；下游机器人和前端消费     |
| `control` | 系统生命周期事件     | 由 `BaseRobot` 自动写入；SSE 桥接和监控消费 |


`control` 流由框架管理 —— 机器人会自动发送 `robot_start`、`robot_stop`、`robot_error` 生命周期信号。

### 信号 Schema

每条流消息对应一个 `Signal`：


| 字段               | 类型     | 说明                                    |
| ---------------- | ------ | ------------------------------------- |
| `type`           | `str`  | 信号类型，如 `data_update`、`process_result` |
| `source`         | `str`  | 发送方的 `robot_type`                     |
| `task_id`        | `str`  | 所属任务 ID                               |
| `timestamp`      | `str`  | ISO 8601 UTC 时间戳                      |
| `data`           | `dict` | 业务数据（任意 JSON）                         |
| `schema_version` | `str`  | `"1.0"` — 生产者与消费者保持一致                 |
| `id`             | `str`  | Redis Stream 消息 ID（读取时填充）             |


### 信号流示例

```
ticker_bot                             transform_bot
    │  （自驱动 — 无 input_streams）          │  （信号驱动 — 监听 data 流）
    │                                        │
    │ emit(DATA, data_update)                │
    └──────── data 流 ──────────────────────►│ on_signal("data", signal)
                                             │
                                             │ emit(OUTPUT, process_result)
                                             └──── output 流 ──────────────► SSE 桥接 ──► 前端

两个机器人都会自动写入控制流：
    robot_start / robot_stop / robot_error  ──► control 流 ──► 前端
```

### SSE 事件类型

SSE 桥接将 Redis Stream 信号映射为前端事件：


| SSE 事件           | 来源信号                                         | 关键载荷字段                            |
| ---------------- | -------------------------------------------- | --------------------------------- |
| `data_update`    | `data_update` 信号                             | `robot_type`、`task_id`、`data {}`  |
| `process_result` | `process_result` 信号                          | `robot_type`、`task_id`、`data {}`  |
| `robot_status`   | `robot_start` / `robot_stop` / `robot_error` | `robot_type`、`state`、`last_error` |
| `task_status`    | `task_status` 信号                             | 完整 `TaskStatus` JSON              |
| `task_end`       | Redis 状态键轮询（非 Stream）                        | `task_id`、`state`                 |
| `heartbeat`      | 当前轮询无新消息                                     | `ts`                              |


> **注意：** `task_end` 通过轮询 Redis 状态键合成，不从流日志转发。这样可以避免休眠/唤醒后重连时重放过期的终态信号。

## 机器人开发

### 机器人的工作方式

每个机器人都是 `BaseRobot` 的子类 —— 一个统一、通用的接口。没有预定义的分类或原型。每个机器人的独特之处在于它如何使用信号：

- **自驱动机器人**（`input_streams = []`）—— 内部自主驱动。按自己的节奏生成数据，不订阅任何流。例如：周期性数据轮询、传感器读取、定时内容生成。
- **信号驱动机器人**（`input_streams = [...]`）—— 响应其他机器人的信号。订阅一个或多个流并处理输入数据。例如：数据变换、LLM 分析、格式转换。

机器人也可以同时兼具两者 —— 自主生产数据的同时响应外部信号。框架不施加任何约束；`input_streams` 和 `output_streams` 只是声明机器人读取和写入哪些流。

机器人内部运行确定性逻辑（如 `1 + 1 = 2`，保障可靠性）还是 AI 驱动的推理（产生创造性、多变的输出），完全取决于它的实现。两者都是同一个 `BaseRobot` 基类的同等有效用法。

### 添加 Python 机器人

在 `swarmbot/robots/my_bot/` 下创建 `__init__.py` 和 `robot.py`，`TaskComposer` 会自动发现它。

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

### 添加 Rust 机器人

继承 `RustRobotProxy` —— Python 管理进程生命周期，Rust 二进制直接操作 Redis。

```python
class TradingBot(RustRobotProxy):
    robot_type = "trading_bot"
    rust_binary = "/path/to/target/release/trading-bot"
    input_streams = [StreamName.DATA]
    output_streams = [StreamName.OUTPUT]
```

Rust 进程通过环境变量接收 `TASK_ID`、`REDIS_URL`、`INPUT_STREAMS`、`OUTPUT_STREAMS` 和 `BOT_*` 配置。它必须向 control 流写入生命周期信号（`robot_start`/`robot_stop`/`robot_error`），并响应 `SIGTERM` 实现优雅关闭。

### 添加自定义信号类型

1. 在 `swarmbot/shared/channels.py` 的 `SignalType` 中添加枚举值
2. 在 `swarmbot/api/routes/live_stream.py` 的 `_signal_to_sse()` 中添加映射
3. 在接收方机器人的 `on_signal()` 中处理 `signal.type == "your_type"`

### 运行指标

覆盖 `get_runtime_metrics()` 可在前端状态面板中展示自定义计数器：

```python
def get_runtime_metrics(self) -> dict[str, Any]:
    return {"processed": self._count, "last_value": self._last}
```

对于高频机器人，设置 `status_broadcast_min_interval = 2.0` 可节流状态推送，不影响信号处理管线速度。

## 开发

```bash
# 语法检查（每次提交前的最低要求）
uv run python -m compileall swarmbot scripts

# 代码检查与格式化
uv run ruff check --fix swarmbot scripts
uv run ruff format swarmbot scripts

# 测试
uv run pytest
uv run pytest tests/test_file.py::test_name -q
uv run pytest -x                                # 第一个失败即停止

# 提交演示任务
uv run python scripts/publish_demo_task.py
```

## 环境变量


| 变量                             | 默认值                        | 说明                 |
| ------------------------------ | -------------------------- | ------------------ |
| `REDIS_URL`                    | `redis://localhost:6379/0` | Redis 连接地址         |
| `EXECUTION_DEDUPE_TTL_SECONDS` | `300`                      | 防止重复启动任务的去重 TTL（秒） |


## 许可证

[MIT](LICENSE)