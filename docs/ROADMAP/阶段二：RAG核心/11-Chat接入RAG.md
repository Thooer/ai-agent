# Chat 接入 RAG Context

把 hybrid search 的结果注入 LLM system prompt，返回带引用来源的回答。

---

## 流程

```
/ai/chat 请求
  │
  ├── hybrid_search(user_id, last_user_message)
  │       │
  │       ├── 有相关结果（rrf_score >= 阈值）→ 构建 RAG context
  │       └── 无相关结果                    → context = ""，走普通对话
  │
  ├── 构建 system prompt（含 context）
  │
  ├── stream_chat(messages)
  │       └── SSE delta/done/error 事件流
  │
  └── background task: 落库（含 retrieved_chunk_ids）
```

---

## System Prompt 结构

```
你是一个知识库助手。请根据以下参考内容回答用户问题。
如果参考内容不足以回答，请直接说明，不要编造。
回答末尾用 [来源：文档名 chunk#序号] 标注引用。

=== 参考内容 ===
[1] 来自《文档A》第3段：
{chunk_content}

[2] 来自《文档B》第7段：
{chunk_content}
...
=================
```

无相关内容时不注入参考内容段，直接走普通对话，不强制拒答（让 LLM 自己判断）。

---

## SSE 事件扩展

接入 RAG 后，检索过程通过 SSE 流向前端展示（阶段二目标中的"流式展示工具调用过程"）：

```
data: {"type": "retrieval_start"}
data: {"type": "retrieval_done", "chunk_count": 3}
data: {"type": "delta", "content": "..."}
data: {"type": "done", "citations": [{doc_name, chunk_index, start_char, end_char}, ...]}
```

`type=done` 事件携带 citations 列表，前端可以渲染引用跳转链接。

---

## 引用落库

`messages` 表暂不加 citations 字段（JSON 列），先把 retrieved_chunk_ids 存日志，后续需要时再加迁移。

---

## 无 RAG 降级

`ChatRequest` 新增可选字段 `use_rag: bool = True`，设为 False 时跳过检索，直接走普通对话。

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `services/rag_chat.py` | 新建，`build_rag_context(chunks) → str`，构建 system prompt |
| `routers/ai_chat.py` | 接入 `hybrid_search`，发 retrieval_start/done 事件，done 事件带 citations |
| `schemas/dto.py` | ChatRequest 新增 use_rag 字段；SseDone 新增 citations 字段；新增 SseRetrievalStart/Done |
