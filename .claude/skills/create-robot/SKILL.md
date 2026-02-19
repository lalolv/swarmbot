---
name: create-robot
description: Use when user asks to create a new robot, add a robot, write a bot, or implement a new robot type in this system. Covers Python robots and Rust robots. Triggered by phrases like "create a robot", "add a new bot", "write a robot", "implement a Rust robot", or "how do I add a robot".
tools: Read, Write, Bash
---

# Create Robot

为 pm-sports-bots 系统创建新机器人。机器人类型只有两种：**Python** 和 **Rust**。

## 执行前必须收集的参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 机器人基础名称（不含 `_bot`），snake_case | `price_tracker` |
| `type` | 机器人类型 | `python` / `rust` |
| `input_streams` | 订阅的流名列表（无则为空） | `data`, `control` |
| `output_streams` | 发布的流名列表 | `output`, `signals` |
| `description` | 一句话功能描述 | 订阅价格流，计算移动平均线 |

若用户未提供，询问后再继续。

---

## 命名规则（强制）

- 目录名 = `{name}_bot`，全小写 snake_case
- `robot_type` 必须与目录名**完全一致**（`composer.py` 启动时会校验，不一致会抛 `ValueError`）
- 目录存放位置：`pm_sports_bots/robots/{name}_bot/`

---

## 机器人类型

### Python 机器人

继承 `BaseRobot`，通过 `input_streams` 决定数据驱动方式：

- **无 `input_streams`**：机器人自行驱动，在 `setup()` 中用 `asyncio.create_task()` 启动循环，适合轮询外部 API、定时发送数据
- **有 `input_streams`**：机器人响应外部信号，实现 `on_signal()` 处理收到的每条信号，适合订阅数据流、信号变换、分析

**文件结构：**
```
{name}_bot/
├── README.md
├── __init__.py
└── robot.py
```

### Rust 机器人

继承 `RustRobotProxy`，Python 侧只声明元数据，实际逻辑在 `src/main.rs` 中。

**文件结构：**
```
{name}_bot/
├── README.md
├── __init__.py
├── robot.py         ← Python 代理（仅声明，无业务逻辑）
├── Cargo.toml
└── src/
    └── main.rs
```

---

## 创建流程

### Step 1：确认流名有效

检查 `pm_sports_bots/shared/channels.py` 中的 `StreamName` 枚举，确认所用流名已定义：

```bash
grep -A 20 "class StreamName" pm_sports_bots/shared/channels.py
```

若不存在，提示用户先在 `StreamName` 中添加。

### Step 2：创建目录

```bash
mkdir -p pm_sports_bots/robots/{name}_bot
# Rust 机器人额外执行：
mkdir -p pm_sports_bots/robots/{name}_bot/src
```

### Step 3：写入文件

按对应类型的模板（见 `references/`）写入所有文件。

### Step 4：语法检查

```bash
uv run python -m compileall pm_sports_bots/robots/{name}_bot -q
```

### Step 5：验证自动注册

```bash
uv run python -c "
from pm_sports_bots.robots.composer import TaskComposer
types = TaskComposer.available_robot_types()
assert '{name}_bot' in types, f'注册失败，当前: {types}'
print('注册成功:', types)
"
```

### Step 6（仅 Rust）：编译验证

```bash
cd pm_sports_bots/robots/{name}_bot && cargo build --release
```

---

## 关键约束

| 约束 | 说明 |
|------|------|
| `robot_type == 目录名` | `composer.py` 自动发现时强制校验，不一致抛 `ValueError` |
| `__init__.py` 必须导出类 | `_discover_robots()` 通过 `importlib` 加载后扫描 `vars(module)` |
| 无需修改 `composer.py` | 自动发现扫描 `*_bot/` 目录，创建后立即生效 |
| Rust 需先编译 | `robot.py` 中 `rust_binary` 路径指向 `target/release/`，需 `cargo build --release` |

---

## 参考模板

- `references/python-self-driven.md` — Python 自驱型机器人完整模板（无 input_streams）
- `references/python-signal-driven.md` — Python 信号驱动型机器人完整模板（有 input_streams）
- `references/rust-robot.md` — Rust 机器人完整模板（含 Cargo.toml + main.rs）
- `references/readme-template.md` — README.md 标准格式
