# README.md 标准模板

## Python 机器人

```markdown
# {Bot Name}

{一句话描述机器人的功能。}

## 类型
Python（asyncio）

## 输入流
| 流     | 信号类型    | 数据字段                               |
|--------|-------------|----------------------------------------|
| data   | data_update | value, min_value, max_value, timestamp |

（无输入流的 Producer 写"无"）

## 输出流
| 流     | 信号类型       | 数据字段                  |
|--------|----------------|---------------------------|
| output | process_result | input_value, result_value |

## 配置参数
| 参数         | 类型  | 默认值 | 说明           |
|--------------|-------|--------|----------------|
| poll_interval| float | 5.0    | 轮询间隔（秒） |

## 注册名称
`{name}_bot`
```

---

## Rust 机器人

```markdown
# {Bot Name}

{一句话描述机器人的功能。}

## 类型
Rust（tokio async）

## 输入流
| 流   | 信号类型    | 数据字段                               |
|------|-------------|----------------------------------------|
| data | data_update | value, min_value, max_value, timestamp |

## 输出流
| 流     | 信号类型       | 数据字段              |
|--------|----------------|-----------------------|
| output | process_result | value, result, action |

## 配置参数（通过环境变量传入）
| 参数    | 环境变量   | 默认值 | 说明         |
|---------|------------|--------|--------------|
| window  | BOT_WINDOW | 10     | 滑动窗口大小 |

## 构建
```bash
cd pm_sports_bots/robots/{name}_bot
cargo build --release
```

编译产物：`target/release/{name}-bot`

## 注册名称
`{name}_bot`
```
