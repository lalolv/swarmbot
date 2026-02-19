# Rust 机器人模板

Rust 进程直接连接 Redis，独立完成所有信号读写。Python 侧只管进程生命周期。

## 文件结构

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

## robot.py（Python 代理）

```python
"""{描述}

实际算法在 src/main.rs 中实现。
"""

from __future__ import annotations

import os

from pm_sports_bots.robots.rust_proxy import RustRobotProxy
from pm_sports_bots.shared.channels import StreamName

_BIN = os.path.join(os.path.dirname(__file__), "target/release/{name}-bot")


class {ClassName}(RustRobotProxy):
    """{描述}"""

    robot_type = "{name}_bot"                          # 必须与目录名完全一致
    rust_binary = os.path.abspath(_BIN)

    input_streams = [StreamName.{INPUT_STREAM}]
    output_streams = [StreamName.{OUTPUT_STREAM}]

    # 降低 Python 侧状态广播频率
    status_broadcast_min_interval = 5.0
```

## __init__.py

```python
from .robot import {ClassName}

__all__ = ["{ClassName}"]
```

---

## Cargo.toml

```toml
[package]
name = "{name}-bot"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "{name}-bot"
path = "src/main.rs"

[dependencies]
tokio       = { version = "1", features = ["full"] }
redis       = { version = "1", features = ["tokio-comp", "streams"] }
serde       = { version = "1", features = ["derive"] }
serde_json  = "1"
chrono      = { version = "0.4", features = ["serde"] }
tracing     = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
anyhow      = "1"

[profile.release]
opt-level      = 3
lto            = true
codegen-units  = 1
```

---

## src/main.rs（骨架）

```rust
//! {描述}
//!
//! 环境变量：
//!   TASK_ID        - 任务 ID（必须）
//!   REDIS_URL      - Redis 连接地址（默认 redis://localhost:6379/0）
//!   ROBOT_TYPE     - 机器人类型标识（默认 {name}_bot）
//!   INPUT_STREAMS  - 逗号分隔输入流，默认 "{input_stream}"

use std::collections::HashMap;
use std::env;
use std::time::Duration;

use anyhow::{Context, Result};
use chrono::Utc;
use redis::aio::MultiplexedConnection;
use serde_json::{json, Value};
use tokio::signal;
use tokio::sync::watch;
use tracing::{info, warn, error};

const STREAM_PREFIX: &str = "pm_sports_bots";

fn stream_key(task_id: &str, stream_name: &str) -> String {
    format!("{STREAM_PREFIX}:task:{task_id}:stream:{stream_name}")
}

// ─── Signal 协议（与 Python Signal.to_fields() 一致）───────────────────────

struct Signal<'a> {
    signal_type: &'a str,
    source: &'a str,
    task_id: &'a str,
    data: Value,
}

impl<'a> Signal<'a> {
    fn to_fields(&self) -> Vec<(String, String)> {
        vec![
            ("type".into(), self.signal_type.into()),
            ("source".into(), self.source.into()),
            ("task_id".into(), self.task_id.into()),
            ("timestamp".into(), Utc::now().format("%Y-%m-%dT%H:%M:%S%.6fZ").to_string()),
            ("schema_version".into(), "1.0".into()),
            ("data".into(), self.data.to_string()),
        ]
    }
}

async fn emit(
    conn: &mut MultiplexedConnection,
    stream: &str,
    robot_type: &str,
    task_id: &str,
    signal_type: &str,
    data: Value,
    maxlen: usize,
) -> Result<String> {
    let fields = Signal { signal_type, source: robot_type, task_id, data }.to_fields();
    let msg_id: String = redis::cmd("XADD")
        .arg(stream)
        .arg("MAXLEN").arg("~").arg(maxlen)
        .arg("*")
        .arg(&fields)
        .query_async(conn)
        .await
        .with_context(|| format!("xadd 失败: stream={stream}"))?;
    Ok(msg_id)
}

// ─── 主循环 ─────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_target(false)
        .with_writer(std::io::stderr)
        .init();

    let task_id    = env::var("TASK_ID").context("TASK_ID 环境变量未设置")?;
    let redis_url  = env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379/0".into());
    let robot_type = env::var("ROBOT_TYPE").unwrap_or_else(|_| "{name}_bot".into());

    let input_stream_names: Vec<String> = env::var("INPUT_STREAMS")
        .unwrap_or_else(|_| "{input_stream}".into())
        .split(',')
        .filter(|s| !s.is_empty())
        .map(String::from)
        .collect();

    let output_stream = stream_key(&task_id, "{output_stream}");
    let control_stream = stream_key(&task_id, "control");
    let input_streams: Vec<String> = input_stream_names.iter()
        .map(|n| stream_key(&task_id, n))
        .collect();

    info!("Rust 机器人启动: type={} task={} inputs={:?}", robot_type, task_id, input_stream_names);

    let client = redis::Client::open(redis_url.as_str()).context("Redis 客户端创建失败")?;
    let mut conn = client.get_multiplexed_async_connection().await.context("Redis 连接失败")?;

    // 启动信号
    emit(&mut conn, &control_stream, &robot_type, &task_id, "robot_start",
        json!({ "robot_type": &robot_type }), 500).await?;

    let (shutdown_tx, mut shutdown_rx) = watch::channel(false);
    tokio::spawn(async move {
        let _ = signal::ctrl_c().await;
        let _ = shutdown_tx.send(true);
    });

    let mut last_ids: HashMap<String, String> = input_streams.iter()
        .map(|s| (s.clone(), "0".to_string()))
        .collect();

    let mut signals_in: u64 = 0;
    let mut signals_out: u64 = 0;
    let poll_ms = 100u64;

    loop {
        if *shutdown_rx.borrow() { break; }

        if input_streams.is_empty() {
            tokio::select! {
                _ = shutdown_rx.changed() => break,
                _ = tokio::time::sleep(Duration::from_millis(poll_ms)) => {}
            }
            continue;
        }

        let stream_keys_vec: Vec<&str> = last_ids.keys().map(|s| s.as_str()).collect();
        let stream_ids_vec: Vec<&str>  = stream_keys_vec.iter().map(|k| last_ids[*k].as_str()).collect();

        let result: redis::RedisResult<
            Option<Vec<(String, Vec<(String, HashMap<String, redis::Value>)>)>>,
        > = redis::cmd("XREAD")
            .arg("COUNT").arg(100)
            .arg("STREAMS")
            .arg(&stream_keys_vec)
            .arg(&stream_ids_vec)
            .query_async(&mut conn)
            .await;

        match result {
            Ok(None) => {
                tokio::select! {
                    _ = shutdown_rx.changed() => break,
                    _ = tokio::time::sleep(Duration::from_millis(poll_ms)) => {}
                }
            }
            Ok(Some(stream_results)) => {
                for (stream_key_str, messages) in stream_results {
                    for (msg_id, fields) in messages {
                        *last_ids.entry(stream_key_str.clone()).or_default() = msg_id;
                        signals_in += 1;

                        // 🔧 自定义点: 处理信号
                        let sig_type = match fields.get("type") {
                            Some(redis::Value::BulkString(b)) => String::from_utf8_lossy(b).to_string(),
                            _ => continue,
                        };

                        if sig_type == "data_update" {
                            // 处理逻辑...
                            emit(&mut conn, &output_stream, &robot_type, &task_id, "process_result",
                                json!({ "result": "ok" }), 1000).await?;
                            signals_out += 1;
                        }

                        // 每 10 条向 control stream 报告状态
                        if signals_in % 10 == 0 {
                            let _ = emit(&mut conn, &control_stream, &robot_type, &task_id, "robot_status",
                                json!({
                                    "robot_type": &robot_type,
                                    "state": "running",
                                    "task_id": &task_id,
                                    "signals_in": signals_in,
                                    "signals_out": signals_out,
                                }), 500).await;
                        }
                    }
                }
            }
            Err(e) => {
                error!("xread 失败: {}", e);
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }
    }

    info!("Rust 机器人正在关闭...");

    emit(&mut conn, &control_stream, &robot_type, &task_id, "robot_stop",
        json!({ "robot_type": &robot_type }), 500).await?;

    info!("Rust 机器人已停止: signals_in={} signals_out={}", signals_in, signals_out);
    Ok(())
}
```

---

## 关键契约（Rust 进程必须遵守）

| 规则 | 说明 |
|------|------|
| Stream key 格式 | `pm_sports_bots:task:{task_id}:stream:{name}` |
| Signal 字段 | `type`, `source`, `task_id`, `timestamp`, `schema_version`, `data`(JSON) |
| 启动 | 向 control 流写 `robot_start` 信号 |
| 停止 | 收到 SIGTERM 后优雅关闭，写 `robot_stop` 信号 |
| 状态同步 | 每 N 条信号向 control 流写 `robot_status`（含 `signals_in/out`）|
| 初始游标 | XREAD 使用 `"0"` 而非 `"$"`，确保不遗漏已有消息 |
| 连接类型 | 使用 `MultiplexedConnection`，**不能用 `XREAD BLOCK`** |

## 编译

```bash
cd pm_sports_bots/robots/{name}_bot
cargo build --release
# 产物：target/release/{name}-bot
```
