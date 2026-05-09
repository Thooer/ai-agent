# 架构决策记录

> 记录关键的架构选择和背后的理由，供面试讲解和开发决策参考。
> 不记录代码细节（看代码本身），只记录"为什么这么做"。

---

## 项目定位

这是一个**求职导向的工程项目**，目标不是做最好用的系统，而是做一个能在简历和面试里讲出深度的项目。

架构决策的优先级：**能讲清楚 > 工程深度 > 功能完整 > 技术先进**。

---

## 整体架构

### 核心设计目标：一套代码，两种部署场景

这个项目的架构目标是**维护一套后端代码，同时支持网页端和 PC 本地端两种部署形态**。两端共用同一套 Agent 逻辑和 RAG 服务，差异只在部署位置和暴露方式。

### 场景一：网页端

```
网页端用户
    │
    ▼
前端（Next.js）
    │  SSE 流式
    ▼
后端 API（FastAPI）—— 部署在服务器
    │
    ├── Agent 服务（工具调用 / 工作流编排）
    │       │
    │       └── RAG 服务（检索 / 生成）
    │               │
    │               └── PostgreSQL + pgvector（向量存储）
    │
    └── Redis（任务状态 / 限流 / 缓存）
```

- RAG 和 Agent 全在服务器，前端只暴露类 ChatGPT 的对话接口
- RAG 不直接暴露给前端，减少攻击面
- 可选：前端加"调用知识库"开关，但 RAG 逻辑仍在后端

### 场景二：PC 本地 Agent

```
PC 本地
    │
    ├── Agent（PC 软件 / 桌面客户端）
    │       │  API 调用
    │       ├── 云端 RAG 服务（服务器）
    │       │       └── 公司文档 / 共享知识库
    │       │
    │       └── 本地 RAG（本地向量库）
    │               └── 个人项目文档 / 私有文件
    │
    └── 本地语义搜索（扩展到云端，对 Agent 透明）
```

- RAG 部署在服务器，Agent 是 PC 端软件（架构类似 Claude Code）
- 云端存公司/共享文档，本地存个人项目文档
- 两套 RAG 对 Agent 透明，统一索引：Agent 发一次检索请求，后端路由到云端或本地，结果合并返回
- PC 端壳子用 Tauri 或 Electron，复用网页端大部分前端代码

### 两端差异对比

| | 网页端 | PC 本地端 |
|--|--------|-----------|
| RAG 位置 | 服务器 | 服务器（公共）+ 本地（私有）|
| Agent 位置 | 服务器 | PC 本地 |
| 前端暴露 | 对话接口 | 本地文件索引 + 对话接口 |
| 差异化功能 | 多用户、知识库管理界面 | 本地文件实时索引 |

**决策**：RAG 和 Agent 都在后端，不暴露给前端。原因：
- API key、prompt、工作流逻辑不能放前端
- 后端统一，PC 端和网页端复用同一套 API
- 面试讲"工作流编排在后端"比"前端画流程图"值钱

---

## RAG 设计

### 为什么自己实现检索逻辑而不直接用 LangChain

面试高频考点。自己实现能讲清楚每一步，用框架包一下讲不出细节。

自己实现的部分：
- **Chunking 策略**：固定窗口 + overlap，chunk size 和 overlap 可配置
- **Hybrid search 融合**：BM25（关键词）+ 向量（语义）+ RRF 融合，融合和截断逻辑自己写
- **Ingestion pipeline**：文档解析 → 清洗 → chunk → embed → 入库，支持增量更新

直接用现成的：
- 向量数据库：pgvector（已有 PostgreSQL，集成成本低，面试能讲"统一存储"）
- Embedding 模型：BGE 或 API（不造这个轮子）
- LLM 调用：直接调 API（不造这个轮子）

### 向量存储选型：pgvector

选 pgvector 而不是 Chroma / Qdrant 的原因：
- 项目已有 PostgreSQL，不引入新的基础设施
- 向量和关系数据在同一个库，metadata 过滤（文档 ID、chunk 序号）用 SQL 直接写
- 面试能讲"统一存储降低运维复杂度"

### Hybrid Search 设计

```
用户 query
    │
    ├── 向量检索（语义相似度，top-k）
    │
    └── BM25 检索（关键词匹配，top-k）
            │
            ▼
        RRF 融合（Reciprocal Rank Fusion）
            │
            ▼
        Rerank（可选，bge-reranker）
            │
            ▼
        返回 top-k chunks + 来源 metadata
```

RRF 公式：`score(d) = Σ 1 / (k + rank(d))`，k=60 是经验值。

### 引用溯源

每个 chunk 存储 metadata：`{doc_id, doc_name, chunk_index, start_line, end_line}`。
回答时把引用的 chunk 来源一起返回，前端可以点击跳转到原文档对应位置。

---

## Agent 设计

### 为什么先手写 Agent loop 再用 LangGraph

面试必问："你的 Agent 是怎么实现的？"

先手写一遍 ReAct loop，能讲清楚：
- 工具注册机制（JSON Schema 描述工具）
- LLM 如何决定调用哪个工具
- 工具结果如何回传 LLM
- 上下文超长时怎么截断
- 工具调用失败怎么重试

之后用 LangGraph 重构，能讲清楚：
- 为什么 LangGraph 比手写更适合复杂流程（状态持久化、条件分支、human-in-the-loop）
- State / Node / Edge 的设计

### Agent 工作流放后端

工作流涉及多步 LLM 调用、状态持久化，全放后端。
- 简单版：Agent loop 本身就是工作流
- 进阶版：轻量 DAG / 状态机，支持"检索 → 判断是否需要再检索 → 生成 → 自检"（Self-RAG 思路）
- 不做：可视化工作流编辑器（工作量大，和核心能力无关）

---

## 前端设计原则

**卷交互细节和工程闭环，不卷 UI 样式。**

重点做：
1. **流式响应**：SSE，展示工具调用过程（"正在检索..."、"读取文档 X 第 Y 行"）
2. **检索调试面板**：输入 query 直接看召回 top-k 和各路分数——面试神器，体现懂评估
3. **引用溯源**：点击引用跳到原文档对应位置
4. **知识库管理**：上传、解析进度、chunk 预览

不做：复杂动画、精美 UI、可视化工作流编辑器。

---

## 技术栈选型汇总

| 层 | 选型 | 理由 |
|----|------|------|
| 后端框架 | FastAPI | 异步原生、Pydantic 集成、StreamingResponse 方便 |
| 数据库 | PostgreSQL | 已有，pgvector 扩展统一存向量 |
| 向量存储 | pgvector | 不引入新基础设施，SQL 过滤方便 |
| 缓存 / 队列 | Redis | 任务状态、限流、embedding 缓存 |
| Agent 框架 | 手写 → LangGraph | 先理解原理，再用框架 |
| Embedding | BGE / API | 不造这个轮子 |
| 前端 | Next.js + Tailwind | 已有，不换 |
| 部署 | Docker Compose | 一键起全家桶 |
| 可观测 | Langfuse 或自实现 | 全链路 trace，面试能讲数字 |

---

## 面试时能讲的工程亮点

- 自实现 hybrid search 融合逻辑（BM25 + 向量 + RRF），能讲 chunk size 选择依据和 recall@5 数字
- 手写 Agent loop 后再用 LangGraph 重构，能对比两者的差异
- pgvector 统一存储，向量检索 + metadata 过滤用 SQL 直接写
- 流式响应展示工具调用过程，自己处理过 backpressure 和断线重连
- 结构化输出 + Pydantic 校验 + 失败重试，能讲 LLM JSON 不稳定的处理策略
