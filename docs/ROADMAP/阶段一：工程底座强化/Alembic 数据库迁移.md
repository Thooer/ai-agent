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
  env.py          # 配置异步引擎、导入所有 ORM 模型
  versions/       # 迁移文件，按时间戳命名
alembic.ini       # sqlalchemy.url 从环境变量读取，不硬编码
```

---

## 异步配置

SQLAlchemy 用的是异步引擎（asyncpg），Alembic 默认同步，需要在 `env.py` 里用 `run_async_migrations` 模式：

```python
# env.py 核心逻辑
from alembic import context
from core.database import engine  # 异步引擎

def run_migrations_online():
    connectable = engine.sync_engine  # 取同步引擎给 Alembic 用
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
```

---

## lifespan 变更

`main.py` 的 lifespan 移除 `create_all`，改为只初始化连接和 pgvector 扩展：

```python
# 移除：await conn.run_sync(Base.metadata.create_all)
# 保留：CREATE EXTENSION IF NOT EXISTS vector（pgvector 初始化）
```

建表由 `alembic upgrade head` 负责，不在应用启动时自动执行。

Docker Compose 里 backend 服务启动命令前加 `alembic upgrade head`，确保每次启动都是最新表结构。

---

## 第一批迁移文件规划

| 版本 | 内容 |
|------|------|
| 0001_initial | 从现有 users / conversations / messages 三张表生成基线 |
| 0002_messages_status | 新增 messages.status、messages.error_message（配合异常处理任务）|

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
| `alembic/env.py` | 新建，配置异步引擎、导入 Base |
| `alembic/versions/0001_initial.py` | 新建，三张表的基线 |
| `alembic/versions/0002_messages_status.py` | 新建，添加 status / error_message 字段 |
| `main.py` | 移除 `create_all`，保留 pgvector 扩展初始化 |
| `requirements.txt` | 新增 `alembic` |
