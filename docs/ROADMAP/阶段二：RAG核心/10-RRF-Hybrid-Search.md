# RRF Hybrid Search

向量检索 + BM25 两路结果，用 RRF（Reciprocal Rank Fusion）融合，返回 final top-k。

---

## RRF 公式

```
score(d) = Σ  1 / (k + rank(d))
```

- `k = 60`（经验值，降低顶部排名差异的影响）
- 对每条检索结果，把它在各路中的排名代入公式求和
- 只出现在一路的文档也参与计算（另一路视为未排名，不加分）

---

## 融合流程

```
query
  │
  ├── embed(query) → vector_search(top_k=10) → [(chunk_id, rank), ...]
  │
  └── bm25_search(top_k=10)              → [(chunk_id, rank), ...]
          │
          ▼
      RRF 融合
          │  对所有出现的 chunk_id 计算 RRF score
          ▼
      按 RRF score 降序排列，取 top-5
          │
          ▼
      从数据库取 top-5 chunks 的完整内容 + metadata
          │
          ▼
      返回 list[RetrievedChunk]
```

---

## 输出结构

```python
@dataclass
class RetrievedChunk:
    chunk_id: UUID
    doc_id: UUID
    doc_name: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    rrf_score: float
    vector_rank: int | None    # None 表示未进入向量 top-k
    bm25_rank: int | None      # None 表示未进入 BM25 top-k
```

`vector_rank` 和 `bm25_rank` 保留原始排名，供检索调试面板展示（面试神器）。

---

## 无关问题拒答

检索后判断：若 final top-5 中最高 rrf_score 对应的 vector score < 阈值（默认 0.3），判定为无关问题，返回拒答标志，不注入 context。

阈值可配置（`RAG_RELEVANCE_THRESHOLD`）。

---

## 检索调试接口

```
POST /rag/search
body: {query: str}
Authorization: Bearer <token>

→ {
    chunks: [RetrievedChunk, ...],
    vector_results: [...],   # 原始向量检索结果
    bm25_results: [...]      # 原始 BM25 结果
  }
```

直接暴露两路原始结果，前端检索调试面板可以展示召回分数对比，面试时直接演示。

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `services/hybrid_search.py` | `hybrid_search(user_id, query, ...)` 主入口，调向量检索 + BM25 + RRF 融合 |
| `services/rrf.py` | 纯函数 `rrf_merge(vector_results, bm25_results, k, top_k) → list` |
| `routers/rag.py` | 新建，`POST /rag/search` 调试接口 |
| `core/config.py` | 新增 RAG_RELEVANCE_THRESHOLD、VECTOR_TOP_K、BM25_TOP_K、RRF_K、FINAL_TOP_K |
