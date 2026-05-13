# Ingestion Pipeline

文档解析 → chunking → embedding → pgvector 入库，全程异步，Redis 报进度。

---

## 流程

```
upload 接口
  │  立即返回 task_id
  ▼
background task
  │
  ├── [10%] parse: 文件字节 → 纯文本
  ├── [20%] chunk: 纯文本 → chunk 列表
  ├── [20~90%] embed_batch: 分批 embedding，每批完成更新进度
  ├── [95%] 入库: chunks 批量写 pgvector，更新 document.chunk_count
  └── [100%] complete_task
```

失败在任意步骤：调 `fail_task(task_id, error_message)`，document 记录保留（方便重试），chunks 回滚。

---

## 进度上报

复用阶段一 `services/task_state.py`（HSET）。

embedding 分批时按比例更新进度：

```
进度 = 20 + (已完成批次 / 总批次) * 70
```

前端轮询 `GET /tasks/{task_id}` 获取进度，后续可升级为 SSE 推送（Pub/Sub 已预留）。

---

## 幂等性

同一文档重复上传：

- 按 `(user_id, name, file_size)` 查重，存在则返回已有 doc_id，不重新 ingest
- 如果明确要重新入库（覆盖），先删旧 chunks（CASCADE），再跑 ingestion

---

## 事务边界

chunks 批量入库用一个 SQLAlchemy session，全部成功后 commit，失败则 rollback。

document 的 `chunk_count` 在 chunks commit 后才更新，保证两者一致。

---

## 进度查询接口

```
GET /tasks/{task_id}
→ {status, progress, error}
```

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `services/ingestion.py` | `run_ingestion(doc_id, file_bytes, file_type, user_id, task_id)` 主流程 |
| `routers/documents.py` | 新增 `GET /tasks/{task_id}` 接口 |
