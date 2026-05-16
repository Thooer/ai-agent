# pgvector + RAG 表迁移

> **状态：✅ 已完成**

为 RAG 新建 documents / chunks 两张表，并初始化 pgvector 扩展。

---

## pgvector 初始化

`lifespan` 启动时执行一次：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

用原始 SQL 通过 SQLAlchemy 异步连接执行，幂等，重复执行无副作用。

pgvector 镜像：docker-compose 里 postgres 换为 `pgvector/pgvector:pg16`（Docker Compose 全家桶任务同步处理）。

---

## 新增表结构

### documents

```sql
CREATE TABLE documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    file_type    VARCHAR(20) NOT NULL,   -- pdf / markdown / txt
    chunk_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT now()
);
```

### chunks

```sql
CREATE TABLE chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL,          -- 冗余，检索时直接过滤，不走 join
    doc_id       UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,
    content      TEXT NOT NULL,
    embedding    vector(1024),
    start_char   INTEGER NOT NULL,
    end_char     INTEGER NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT now()
);
```

`user_id` 在 chunks 表冗余存储（不走 join），向量检索时直接加 `WHERE user_id = ?` 过滤，避免和 documents 做 join 影响性能。

---

## 索引

```sql
-- 向量检索：IVFFlat（小数据量够用，面试能讲与 HNSW 的取舍）
CREATE INDEX chunks_embedding_idx ON chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 按用户过滤（检索必过）
CREATE INDEX chunks_user_id_idx ON chunks (user_id);

-- 文档归属查询
CREATE INDEX chunks_doc_id_idx ON chunks (doc_id);
```

IVFFlat 选 lists=100，适合 chunk 数量 < 100 万的场景。面试能说明：HNSW 召回更准但内存占用更高，当前阶段 IVFFlat 够用。

---

## Alembic 迁移

新建 `0003_rag_tables.py`，包含：
1. `CREATE EXTENSION IF NOT EXISTS vector`（通过 `op.execute`）
2. 建 documents 表
3. 建 chunks 表（含 vector 列）
4. 建三个索引

---

## ORM 模型

在 `models/orm.py` 新增 `Document` 和 `Chunk` 两个 ORM 类，使用 `pgvector.sqlalchemy.Vector` 类型映射 embedding 列。

---

## 实现文件

| 文件 | 变更 |
|------|------|
| `models/orm.py` | 新增 Document、Chunk ORM 类 |
| `alembic/versions/0003_rag_tables.py` | 新建，pgvector 扩展 + 两张表 + 三个索引 |
| `main.py` | lifespan 加 CREATE EXTENSION IF NOT EXISTS vector |
| `postgresql/docker-compose.yml` | postgres 镜像换为 pgvector/pgvector:pg16 |
| `requirements.txt` | 新增 pgvector |
