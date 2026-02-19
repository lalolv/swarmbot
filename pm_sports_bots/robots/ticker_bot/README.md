# Ticker Bot

定期生成随机价格数据的示例机器人，模拟数据源，周期性向 `data` 流发送数值信号。

## 类型
Python（asyncio）

## 输入流
无

## 输出流
| 流     | 信号类型    | 数据字段                                      |
|--------|-------------|-----------------------------------------------|
| data   | data_update | value, min_value, max_value, timestamp        |

## 配置参数
| 参数          | 类型  | 默认值 | 说明               |
|---------------|-------|--------|--------------------|
| poll_interval | float | 10.0   | 发送间隔（秒）     |
| min_value     | float | 0.0    | 随机数下界         |
| max_value     | float | 100.0  | 随机数上界         |

## 注册名称
`ticker_bot`
