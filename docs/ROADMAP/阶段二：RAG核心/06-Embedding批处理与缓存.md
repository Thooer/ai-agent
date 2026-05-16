# Embedding 批处理 + 缓存

> **状态：✅ 已完成**

调智谱 embedding-3 API，1024 维向量，走 Redis 缓存避免重复计费。

---

## Embedding Service 设计

封装为 `EmbeddingService`，屏蔽 provider 细节，对外只暴露：

```python
async def embed(text: str) -> list[float]
async def embed_batch(texts: list[str]) -> list[list[float]]
```

provider 从配置决定（当前只实现智谱），后续换模型只改 provider，不改调用方。

---

## 智谱 embedding-3

```
API: POST /embeddings
model: "embedding-3"
input: str 或 list[str]（批量）
dimensions: 1024
```

单次 API 调用最多 batch_size=32 条（智谱限制），超出自动分批。

---

## Redis 缓存集成

直接复用 `services/embedding_cache.py`（阶段一已实现）：

- key：`sha256(text)` → msgpack 序列化向量，TTL 7 天
- 批量写入走 Pipeline
- embed_batch 调用前先批量查缓存，只对 miss 的文本发 API 请求，结果回写缓存

缓存命中率在 ingestion 重跑场景（文档重新入库）下接近 100%，面试能讲这个优化。

---

## 错误处理

- API 超时（10s）：抛 `EmbeddingError`，ingestion pipeline 捕获后 fail task
- API 限流（429）：等待 1s 后重试，最多 3 次
- 向量维度不符（非 1024）：抛 `EmbeddingError`，记 ERROR 日志

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `services/embedding_service.py` | `EmbeddingService` 类，embed / embed_batch，内部处理分批和缓存 |
| `core/config.py` | 新增 EMBEDDING_MODEL、EMBEDDING_DIM、EMBEDDING_BATCH_SIZE |
| `requirements.txt` | 不新增（复用 httpx） |
