# AI Agent

一个基于大语言模型的 AI 聊天应用，支持多用户、多会话管理。

## 功能特性

- 用户管理：创建、删除用户
- 会话管理：新建、重命名、删除会话
- AI 聊天：基于智谱 GLM-5.1 的流式对话
- 消息历史：自动保存到 PostgreSQL

## 技术栈

- **前端**: Next.js 16 + React 19 + TypeScript + Tailwind CSS v4
- **后端**: Python + FastAPI + SQLAlchemy(异步)
- **数据库**: PostgreSQL 16
- **AI 模型**: 智谱 GLM-5.1 (BigModel API)

## 快速开始

### 1. 启动数据库

```bash
cd postgresql
docker compose up -d
```

### 2. 启动后端

```bash
# 创建虚拟环境（首次）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖（首次）
pip install fastapi uvicorn sqlalchemy asyncpg httpx pydantic "pydantic[email]" python-dotenv

# 配置环境变量（首次）
cp .env.example .env
# 编辑 .env 文件，填入你的 BigModel API Key

# 启动服务
python main.py
```

后端运行在 http://localhost:8000

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

前端运行在 http://localhost:3000

## 项目结构

```
ai-agent/
├── main.py              # FastAPI 应用入口
├── core/                # 核心配置
│   ├── config.py        # 环境变量配置
│   └── database.py      # 数据库连接与会话管理
├── models/              # 数据模型
│   └── orm.py           # SQLAlchemy ORM 模型
├── schemas/             # 请求/响应模型
│   └── dto.py           # Pydantic 数据验证模型
├── services/            # 业务逻辑层
│   ├── llm.py           # 大模型调用服务
│   └── message_saver.py # 消息持久化服务
├── routers/             # API 路由层
│   ├── users.py         # 用户管理路由
│   ├── conversations.py # 会话管理路由
│   ├── messages.py      # 消息管理路由
│   └── ai_chat.py       # AI 聊天路由
├── web/                 # Next.js 前端
│   ├── app/             # 页面和布局
│   ├── components/      # React 组件
│   └── lib/api.ts       # API 客户端
├── postgresql/          # 数据库配置
│   └── docker-compose.yml
└── docs/                # 设计文档
```

## 环境变量

### 后端 (.env)

```bash
# 数据库连接
DATABASE_URL=postgresql+asyncpg://thooer:thooer123@localhost:5432/ai_agent

# BigModel API 配置（必填）
BIGMODEL_API_KEY=your_api_key_here
BIGMODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# CORS 配置
CORS_ORIGINS=http://localhost:3000

# 服务监听配置
APP_HOST=127.0.0.1
APP_PORT=8000
```

### 前端 (web/.env.local)

```
PYTHON_API_URL=http://localhost:8000
```

## 数据库配置

| 项目 | 值 |
|------|------|
| 镜像 | postgres:16-alpine |
| 容器名 | ai-agent-postgres |
| 用户 | thooer |
| 密码 | thooer123 |
| 数据库 | ai_agent |
| 端口 | 5432 |

## API 端点

后端提供以下 REST API：

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/users` | 创建用户 |
| GET | `/users` | 获取所有用户 |
| GET/PUT/DELETE | `/users/{id}` | 操作用户 |
| POST | `/conversations` | 创建会话 |
| GET | `/conversations/user/{id}` | 获取用户会话 |
| PUT/DELETE | `/conversations/{id}` | 操作会话 |
| GET | `/messages/conversation/{id}` | 获取会话消息 |
| POST | `/messages` | 创建消息 |
| DELETE | `/messages/{id}` | 删除消息 |
| POST | `/ai/chat` | AI 流式聊天 |
| GET | `/health` | 健康检查 |

## 开发说明

### 后端架构

- **分层设计**: 按职责分为 core/models/schemas/services/routers 五层
- **异步支持**: 全链路异步（FastAPI + SQLAlchemy AsyncSession + httpx AsyncClient）
- **配置管理**: 使用 `python-dotenv` 从 `.env` 加载环境变量
- **数据库**: 启动时自动创建表（`lifespan`），支持连接池
- **流式处理**: AI 响应流式输出，结束后异步保存到数据库

### 前端

- 使用 `use client` 指令，纯客户端渲染
- 通过 SSE 接收流式 AI 响应

## 部署

### 前端构建

```bash
cd web
npm run build
npm run start
```

### 后端部署

```bash
source .venv/bin/activate
python main.py
```

生产环境建议使用 `gunicorn` + `uvicorn.workers.UvicornWorker`：

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 目录说明

| 目录 | 职责 |
|------|------|
| `core/` | 基础设施：配置、数据库连接 |
| `models/` | 数据层：ORM 实体定义 |
| `schemas/` | 接口层：请求/响应数据模型 |
| `services/` | 业务层：可复用的业务逻辑 |
| `routers/` | 接口层：HTTP 路由处理 |
| `web/` | 前端：Next.js 应用 |
| `postgresql/` | 数据库：Docker 配置 |
| `docs/` | 文档：设计文档和计划 |
