# Docker Compose 全家桶

目标：`docker compose up` 一条命令起全部服务（后端 + 前端 + PostgreSQL + Redis），并且 PostgreSQL 启用 pgvector 扩展，为阶段二 RAG 做好准备。

---

## 服务清单

| 服务 | 镜像 | 说明 |
|------|------|------|
| postgres | pgvector/pgvector:pg16 | 替换 postgres:16-alpine，内置 pgvector 扩展 |
| redis | redis:7-alpine | 已有，不变 |
| backend | 本地 Dockerfile | FastAPI，依赖 postgres + redis 健康后启动 |
| frontend | 本地 Dockerfile | Next.js dev server（开发阶段），production 阶段换 build + nginx |

---

## pgvector 镜像替换

原镜像 `postgres:16-alpine` 不含 pgvector，直接换为 `pgvector/pgvector:pg16`，其余配置不变。

连接建立后需执行一次：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

放在 backend 启动时的初始化逻辑里（`lifespan` 里用 `conn.execute` 执行），不依赖手动操作。

---

## 启动顺序与健康检查

postgres 和 redis 需要真正 ready 后 backend 才能连，用 `healthcheck` + `depends_on.condition: service_healthy` 控制。

```
postgres healthcheck：pg_isready -U ${POSTGRES_USER}
redis healthcheck：redis-cli ping
backend depends_on：postgres(healthy) + redis(healthy)
frontend depends_on：backend(started) 即可，不强依赖 healthy
```

---

## 环境变量管理

`.env` 文件由开发者本地维护，不进 git（`.gitignore` 已有）。`docker-compose.yml` 通过 `env_file: .env` 统一注入，各服务按需取用。

提供 `.env.example` 作为模板，列出所有必填项：
```
DATABASE_URL
BIGMODEL_API_KEY
REDIS_URL
REDIS_PROJECT_PREFIX
CORS_ORIGINS
```

---

## 单套 Compose 策略

不拆 dev/prod 两套，理由：
- 当前阶段部署目标是服务器单机，prod 和 dev 差异不大
- 拆两套维护成本高，容易漂移
- 需要 prod 优化时（nginx、gunicorn worker 数量）再拆

前端在 Compose 里用 dev server（`npm run dev`），足够演示和面试使用。

---

## 实现文件

| 文件 | 变更 |
|------|------|
| `postgresql/docker-compose.yml` | 替换 postgres 镜像、添加 backend/frontend 服务、添加 healthcheck |
| `Dockerfile`（后端） | 新建，基于 python:3.12-slim，安装依赖，启动 uvicorn |
| `web/Dockerfile`（前端） | 新建，基于 node:20-alpine，npm install + npm run dev |
| `.env.example` | 新建，列出所有必填环境变量 |
| `core/database.py` | lifespan 里添加 `CREATE EXTENSION IF NOT EXISTS vector` |
