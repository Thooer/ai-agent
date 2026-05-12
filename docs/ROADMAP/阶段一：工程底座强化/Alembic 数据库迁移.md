# Alembic 数据库迁移

替换 `Base.metadata.create_all` 的直接建表方式，引入 Alembic 管理迁移历史，支持表结构增量变更。

---

## 为什么现在引入

当前 `lifespan` 里用 `create_all` 建表，表结构一旦存在就不会更新，加字段只能手动 ALTER TABLE 或删库重建。

阶段一的异常处理任务要给 `messages` 表加 `status` / `error_message` 字段，阶段二 RAG 会新建文档、chunk、向量等多张表，这是引入 Alembic 的合适时机——表结构还不复杂，迁移文件不会很碎。

---

## 目录结构

```
alembic/
  env.py          # 配置同步引擎、导入所有 ORM 模型
  versions/       # 迁移文件，按时间戳命名
alembic.ini       # sqlalchemy.url 从环境变量读取，不硬编码
```

---

## 同步驱动配置

SQLAlchemy 用的是异步引擎（asyncpg），Alembic 默认同步，`env.py` 里用 psycopg2 同步驱动，并自动将 `DATABASE_URL` 中的 `asyncpg` 替换为标准 `postgresql`：

```python
def get_url() -> str:
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    return re.sub(r"postgresql\+asyncpg://", "postgresql://", url)
```

依赖 `psycopg2-binary`（已加入 requirements.txt）。

---

## lifespan 变更

`main.py` 的 lifespan 移除 `create_all`，建表完全由 `alembic upgrade head` 负责：

```python
# 移除：await conn.run_sync(Base.metadata.create_all)
```

Docker Compose 里 backend 服务启动命令前加 `alembic upgrade head`，确保每次启动都是最新表结构。

---

## 迁移文件

| 版本 | 内容 |
|------|------|
| `fd7005fcca4f` 0001_initial | users / conversations / messages 三张表的完整建表 DDL |
| `3cc1f6c84311` 0002_messages_status | 新增 messages.status（VARCHAR 20, NOT NULL, DEFAULT 'completed'）和 messages.error_message（TEXT, NULL）|

**注意**：0001 基线是手写的完整 DDL，不是 autogenerate 的空 pass。原因是 autogenerate 在表已存在时检测不到差异，新库上跑会跳过建表直接执行 0002 导致报错。

---

## 常用命令

```bash
# 生成迁移文件（自动检测 ORM 变更）
alembic revision --autogenerate -m "描述"

# 升级到最新
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 查看当前版本
alembic current
```

---

## 实现文件

| 文件 | 变更 |
|------|------|
| `alembic.ini` | 新建，sqlalchemy.url 读环境变量 |
| `alembic/env.py` | 新建，psycopg2 同步驱动，asyncpg URL 自动替换，导入 Base |
| `alembic/versions/fd7005fcca4f_0001_initial.py` | 新建，三张表完整建表 DDL |
| `alembic/versions/3cc1f6c84311_0002_messages_status.py` | 新建，添加 status / error_message 字段 |
| `main.py` | 移除 `create_all` |
| `requirements.txt` | 新增 `alembic`、`psycopg2-binary` |

---

## 验证结果

- 新库（`ai_agent_test`）：`alembic upgrade head` 从零建表，两个版本顺序执行，messages 表含全部 7 个字段
- 现有库（`ai_agent`）：已在 head，`alembic current` 返回 `3cc1f6c84311 (head)`，平滑迁移无报错
