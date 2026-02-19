# Trading Bot

Rust 实现的量化分析机器人，对输入数据做滑动窗口归一化分析，输出买卖决策信号。

## 类型
Rust（tokio async）

## 输入流
| 流   | 信号类型    | 数据字段                               |
|------|-------------|----------------------------------------|
| data | data_update | value, min_value, max_value, timestamp |

## 输出流
| 流     | 信号类型       | 数据字段                        |
|--------|----------------|---------------------------------|
| output | process_result | value, normalized, avg, action  |

`action` 取值：`buy` / `sell` / `hold`

## 配置参数
| 参数        | 环境变量        | 默认值 | 说明                   |
|-------------|-----------------|--------|------------------------|
| window      | BOT_WINDOW      | 10     | 滑动窗口大小           |
| buy_below   | BOT_BUY_BELOW   | 0.3    | 归一化值低于此 → 买入  |
| sell_above  | BOT_SELL_ABOVE  | 0.7    | 归一化值高于此 → 卖出  |

## 构建
```bash
cd pm_sports_bots/robots/trading_bot
cargo build --release
```

编译产物：`target/release/trading-bot`

## 注册名称
`trading_bot`
