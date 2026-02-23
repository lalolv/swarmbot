# Transform Bot

数据处理示例机器人，订阅 `data` 流，对数值做线性变换后写入 `output` 流。

## 类型
Python（asyncio）

## 输入流
| 流   | 信号类型    | 数据字段                               |
|------|-------------|----------------------------------------|
| data | data_update | value, min_value, max_value, timestamp |

## 输出流
| 流     | 信号类型       | 数据字段                                                      |
|--------|----------------|---------------------------------------------------------------|
| output | process_result | source_type, input_value, coefficient, offset, result_value, timestamp |

## 配置参数
| 参数       | 类型  | 默认值 | 说明                   |
|------------|-------|--------|------------------------|
| multiplier | float | 1.5    | 线性变换系数           |
| offset     | float | 0.0    | 线性变换偏移量         |

## 注册名称
`transform_bot`
