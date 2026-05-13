# Chunking

把解析后的纯文本切成固定大小的 chunk，作为 embedding 和检索的基本单元。

---

## 策略：固定窗口 + overlap

用 `tiktoken` 计 token 数（`cl100k_base` encoding，和 OpenAI/智谱 embedding 对齐）。

```
chunk_size    = 512 token   （可配置）
chunk_overlap = 64 token    （可配置）
```

滑窗逻辑：
1. 将全文 tokenize 为 token id 列表
2. 每次取 [i : i+chunk_size] 作为一个 chunk
3. 下一个 chunk 从 i+chunk_size-chunk_overlap 开始
4. 记录每个 chunk 的 start_char / end_char（从 token offset 反算字符位置）

---

## 为什么按 token 切而不是按字符

- Embedding API 按 token 计费和截断，字符数不等于 token 数（中文 1 字 ≈ 1-2 token）
- 用 tiktoken 切出来的 chunk 不会超过 embedding API 的 token 上限（embedding-3 上限 8192）
- 面试能讲这个选择依据

---

## chunk_size 选择依据（面试必备）

- 太小（< 128）：单个 chunk 缺少上下文，embedding 语义不完整，召回噪声多
- 太大（> 1024）：context 占用大，注入 LLM 的文本噪声多，相关性被稀释
- 512 是经验值，适合技术文档类内容；后续可以用评估集对比 256 / 512 / 768 的 recall@5

---

## 边界处理

- 最后一个 chunk 可能不足 chunk_size，直接保留，不丢弃
- 纯空白/无意义 chunk（token 数 < 16）跳过，记 WARNING 日志
- 单文档 chunk 数量上限：1000（防止超大文件把内存打爆）

---

## 输出结构

```python
@dataclass
class Chunk:
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    token_count: int
```

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `services/chunker.py` | `chunk(text, chunk_size, overlap) → list[Chunk]` |
| `core/config.py` | 新增 CHUNK_SIZE、CHUNK_OVERLAP 配置项 |
| `requirements.txt` | 新增 `tiktoken` |
