Structured Output

让模型输出严格符合特定格式（JSON、YAML 等）的技术，通常结合 Pydantic 或 JSON Schema 约束实现。在 Agent 开发中，它保证后续代码能可靠解析模型输出，避免格式混乱导致的错误。

大白话：Structured Output 就是强迫 AI 按固定格式吐出结果，比如标准的 JSON，让程序好处理。
