//! Rust 交易分析机器人
//!
//! 订阅 SampleProducer 发出的 data_update 信号（stream: data），
//! 对每条信号做滑动窗口统计 + 简单归一化策略，结果写入 output stream。
//!
//! SampleProducer 信号格式（data 字段）：
//!   { "value": f64, "min_value": f64, "max_value": f64, "timestamp": str }
//!
//! 环境变量：
//!   TASK_ID        - 任务 ID（必须）
//!   REDIS_URL      - Redis 连接地址（默认 redis://localhost:6379/0）
//!   ROBOT_TYPE     - 机器人类型标识（默认 rust_trading_bot）
//!   INPUT_STREAMS  - 逗号分隔，默认 "data"
//!   BOT_WINDOW     - 滑动窗口大小（默认 10）
//!   BOT_BUY_BELOW  - 归一化值低于此阈值触发买入（默认 0.3）
//!   BOT_SELL_ABOVE - 归一化值高于此阈值触发卖出（默认 0.7）

use std::collections::{HashMap, VecDeque};
use std::env;
use std::time::Duration;

use anyhow::{Context, Result};
use chrono::Utc;
use redis::aio::MultiplexedConnection;
use serde_json::{json, Value};
use tokio::signal;
use tokio::sync::watch;
use tracing::{info, warn, error};

// ─────────────────────────────────────────────
// Redis Stream Key 格式（与 Python Channels 一致）
// ─────────────────────────────────────────────

const STREAM_PREFIX: &str = "swarmbot";

fn stream_key(task_id: &str, stream_name: &str) -> String {
    format!("{STREAM_PREFIX}:task:{task_id}:stream:{stream_name}")
}

// ─────────────────────────────────────────────
// Signal：与 Python Signal.to_fields() 完全一致
// ─────────────────────────────────────────────

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

// ─────────────────────────────────────────────
// emit / emit_status
// ─────────────────────────────────────────────

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

async fn emit_status(
    conn: &mut MultiplexedConnection,
    control_stream: &str,
    robot_type: &str,
    task_id: &str,
    state: &str,
    signals_in: u64,
    signals_out: u64,
) -> Result<()> {
    emit(conn, control_stream, robot_type, task_id, "robot_status", json!({
        "robot_type": robot_type,
        "state": state,
        "task_id": task_id,
        "signals_in": signals_in,
        "signals_out": signals_out,
        "timestamp": Utc::now().to_rfc3339(),
    }), 500).await?;
    Ok(())
}

// ─────────────────────────────────────────────
// 滑动窗口分析状态
// ─────────────────────────────────────────────

struct AnalysisState {
    window: VecDeque<f64>,
    window_size: usize,
    buy_below: f64,   // 归一化值低于此 → 买入区间
    sell_above: f64,  // 归一化值高于此 → 卖出区间
    total_analyzed: u64,
}

impl AnalysisState {
    fn new(window_size: usize, buy_below: f64, sell_above: f64) -> Self {
        Self {
            window: VecDeque::with_capacity(window_size + 1),
            window_size,
            buy_below,
            sell_above,
            total_analyzed: 0,
        }
    }

    fn push(&mut self, value: f64) {
        self.window.push_back(value);
        if self.window.len() > self.window_size {
            self.window.pop_front();
        }
        self.total_analyzed += 1;
    }

    fn moving_avg(&self) -> f64 {
        if self.window.is_empty() {
            return 0.0;
        }
        self.window.iter().sum::<f64>() / self.window.len() as f64
    }

    /// 窗口内斜率：(最新 - 最早) / 窗口长度，判断趋势方向
    fn trend_slope(&self) -> f64 {
        if self.window.len() < 2 {
            return 0.0;
        }
        let first = *self.window.front().unwrap();
        let last = *self.window.back().unwrap();
        (last - first) / (self.window.len() - 1) as f64
    }

}

// ─────────────────────────────────────────────
// 处理单条 data_update 信号
// ─────────────────────────────────────────────

async fn process_signal(
    conn: &mut MultiplexedConnection,
    output_stream: &str,
    robot_type: &str,
    task_id: &str,
    fields: &HashMap<String, redis::Value>,
    state: &mut AnalysisState,
) -> Result<bool> {
    // 只处理 data_update 信号
    let sig_type = match fields.get("type") {
        Some(redis::Value::BulkString(b)) => String::from_utf8_lossy(b).to_string(),
        _ => return Ok(false),
    };
    if sig_type != "data_update" {
        return Ok(false);
    }

    // 解析 data JSON
    let data_str = match fields.get("data") {
        Some(redis::Value::BulkString(b)) => String::from_utf8_lossy(b).to_string(),
        _ => return Ok(false),
    };
    let data: Value = serde_json::from_str(&data_str).unwrap_or(Value::Null);

    let value     = match data.get("value").and_then(|v| v.as_f64())     { Some(v) => v, None => return Ok(false) };
    let min_value = data.get("min_value").and_then(|v| v.as_f64()).unwrap_or(0.0);
    let max_value = data.get("max_value").and_then(|v| v.as_f64()).unwrap_or(100.0);

    // 更新窗口
    state.push(value);

    // ── 计算 ──
    let range = (max_value - min_value).max(f64::EPSILON);

    // 归一化位置 [0.0, 1.0]：value 在 [min_value, max_value] 中的位置
    let normalized = ((value - min_value) / range).clamp(0.0, 1.0);

    let moving_avg  = state.moving_avg();
    let trend_slope = state.trend_slope();

    let action = if normalized < state.buy_below && trend_slope >= 0.0 {
        "buy"
    } else if normalized > state.sell_above && trend_slope <= 0.0 {
        "sell"
    } else {
        "hold"
    };

    emit(conn, output_stream, robot_type, task_id, "process_result", json!({
        "value":      (value * 100.0).round() / 100.0,
        "normalized": (normalized * 1000.0).round() / 1000.0,
        "avg":        (moving_avg * 100.0).round() / 100.0,
        "action":     action,
    }), 1000).await?;

    info!(
        "分析完成: action={} value={:.2} normalized={:.3} avg={:.2} slope={:.4}",
        action, value, normalized, moving_avg, trend_slope
    );

    Ok(true)
}

// ─────────────────────────────────────────────
// 主循环
// ─────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_target(false)
        .with_writer(std::io::stderr)
        .init();

    let task_id    = env::var("TASK_ID").context("TASK_ID 环境变量未设置")?;
    let redis_url  = env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379/0".into());
    let robot_type = env::var("ROBOT_TYPE").unwrap_or_else(|_| "trading_bot".into());

    let input_stream_names: Vec<String> = env::var("INPUT_STREAMS")
        .unwrap_or_else(|_| "data".into())   // 默认订阅 SampleProducer 的 data stream
        .split(',')
        .filter(|s| !s.is_empty())
        .map(String::from)
        .collect();

    let window_size: usize = env::var("BOT_WINDOW")
        .ok().and_then(|v| v.parse().ok()).unwrap_or(10);
    let buy_below: f64 = env::var("BOT_BUY_BELOW")
        .ok().and_then(|v| v.parse().ok()).unwrap_or(0.3);
    let sell_above: f64 = env::var("BOT_SELL_ABOVE")
        .ok().and_then(|v| v.parse().ok()).unwrap_or(0.7);

    let output_stream  = stream_key(&task_id, "output");
    let control_stream = stream_key(&task_id, "control");
    let input_streams: Vec<String> = input_stream_names.iter()
        .map(|n| stream_key(&task_id, n))
        .collect();

    info!(
        "Rust 机器人启动: type={} task={} inputs={:?} window={} buy<{} sell>{}",
        robot_type, task_id, input_stream_names, window_size, buy_below, sell_above
    );

    let client = redis::Client::open(redis_url.as_str()).context("Redis 客户端创建失败")?;
    let mut conn = client.get_multiplexed_async_connection().await.context("Redis 连接失败")?;

    emit(&mut conn, &control_stream, &robot_type, &task_id, "robot_start",
        json!({ "robot_type": &robot_type }), 500).await?;

    let (shutdown_tx, mut shutdown_rx) = watch::channel(false);
    tokio::spawn(async move {
        let _ = signal::ctrl_c().await;
        let _ = shutdown_tx.send(true);
    });

    // 非阻塞 XREAD 不能用 "$"：每次调用 "$" 都被 Redis 解析为"当前最新 ID"，
    // 导致永远追不上新消息。用 "0" 从流起点读起，顺带暖机滑动窗口。
    let mut last_ids: HashMap<String, String> = input_streams.iter()
        .map(|s| (s.clone(), "0".to_string()))
        .collect();

    let mut analysis = AnalysisState::new(window_size, buy_below, sell_above);
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

                        match process_signal(
                            &mut conn, &output_stream, &robot_type,
                            &task_id, &fields, &mut analysis,
                        ).await {
                            Ok(true)  => signals_out += 1,
                            Ok(false) => {}
                            Err(e)    => warn!("信号处理失败: {}", e),
                        }

                        // 每处理 10 个信号向 control stream 发一次 robot_status，
                        // 让前端展示 Rust 侧真实的 signals_in/out（Python proxy 无法获取）
                        if signals_in % 10 == 0 {
                            let _ = emit_status(
                                &mut conn, &control_stream, &robot_type, &task_id,
                                "running", signals_in, signals_out,
                            ).await;
                        }
                    }
                }
            }
            Err(e) => {
                error!("xread 失败: {}", e);
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }

        if *shutdown_rx.borrow() { break; }
    }

    info!("Rust 机器人正在关闭...");

    let _ = emit_status(&mut conn, &control_stream, &robot_type, &task_id,
        "stopped", signals_in, signals_out).await;

    emit(&mut conn, &control_stream, &robot_type, &task_id, "robot_stop",
        json!({ "robot_type": &robot_type }), 500).await?;

    info!("Rust 机器人已停止: signals_in={} signals_out={} analyzed={}",
        signals_in, signals_out, analysis.total_analyzed);
    Ok(())
}
