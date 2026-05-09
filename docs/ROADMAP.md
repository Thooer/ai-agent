# 开发进度 / 里程碑

> 用于跟踪项目从基础聊天应用演进为完整 AI Agent 系统的进度。
> 每个里程碑有明确的完成标准，完成后打勾 `[x]`。

---

## 当前状态（起点）

- [x] FastAPI 后端分层架构（core / models / schemas / services / routers）
- [x] PostgreSQL + SQLAlchemy 异步 ORM
- [x] 多用户 / 多会话管理
- [x] 智谱 GLM 流式对话（SSE）
- [x] Next.js 前端基础界面
- [x] Docker Compose 启动数据库

---

## 阶段一：工程底座强化

目标：把现有项目升级为"像生产项目"的工程底座，专注服务器侧（网页端场景）。

- [ ] Redis 集成（任务状态缓存 / 限流）
- [ ] 异常处理统一（LLM 超时、JSON 解析失败、工具调用失败的兜底）
- [ ] Docker Compose 一键起全家桶（后端 + 前端 + PostgreSQL + Redis）——仅服务器/网页端部署
- [ ] Alembic 数据库迁移
- [ ] 结构化日志（每次请求记录 token 用量、耗时、工具调用结果）
- [ ] 接入 JWT 鉴权，用户隔离（可在 RAG 跑通后补上）

**完成标准**：`docker compose up` 能起全部服务，pgvector 可用，异常有兜底，日志可观测。

---

## 阶段二：RAG 核心

目标：做出知识库问答能力，这是简历第一个核心模块。

- [ ] 文档解析（PDF / Markdown / TXT）
- [ ] Chunking 策略（固定窗口 + overlap，可配置 chunk size）
- [ ] Embedding 入库（BGE 或 API，存入 pgvector）
- [ ] 向量检索（similarity search + top-k）
- [ ] BM25 关键词检索
- [ ] Hybrid search（向量 + BM25 + RRF 融合，**自己实现融合逻辑**）
- [ ] 引用来源返回（回答中标注来自哪个文档哪个 chunk）
- [ ] 无关问题拒答
- [ ] 知识库管理 API（上传 / 删除 / 查看文档列表）
- [ ] RAG 评估集（至少 20 条 QA，跑 recall@5）

**完成标准**：上传一份技术文档，能准确问答并返回引用片段，recall@5 有数字可讲。

---

## 阶段三：Agent Loop

目标：把 RAG 升级为可控的 Agent 系统。

- [ ] 手写极简 Agent loop（ReAct 模式，不直接上 LangGraph）
  - 工具注册机制
  - LLM 判断是否调用工具
  - 工具结果回传 LLM
  - 错误重试 + 上下文截断策略
- [ ] 工具集成：RAG 检索工具、数据库查询工具、文件读取工具
- [ ] Structured Output（Pydantic 校验 + 失败重试）
- [ ] 流式输出工具调用过程（"正在检索..."、"调用工具 X..."）
- [ ] LangGraph 重构 Agent（在手写版跑通后）
  - State / Node / Edge / Conditional Edge
  - Checkpoint 持久化
  - Human-in-the-loop

**完成标准**：用户提问后，Agent 能自主决定调用哪些工具、完成多步推理并返回带引用的答案。

---

## 阶段四：主项目冲刺

目标：做出一个有深度、能在面试里讲 20 分钟的主项目。

主项目方向（待定，参考 `ARCHITECTURE.md`）：

- [ ] 确定主项目场景
- [ ] 设计 Agent 工作流节点图
- [ ] 实现核心 Agent 流程
- [ ] 可观测：全链路 trace（Langfuse 或自实现）
- [ ] 评测：准备测试集，展示优化前后效果对比
- [ ] 前端：检索调试面板（输入 query 直接看召回 top-k 和各路分数）
- [ ] 前端：引用溯源（点击引用跳到原文档对应位置）

**完成标准**：能用 3 分钟讲清楚架构、每一步 Agent 流转、RAG 设计决策、工程亮点。

### PC 本地端扩展（时间够再做，否则作为"规划中"讲）

> 前端复用同一套 Next.js，Tauri 壳子包起来，API 指向 localhost，不重复开发。

- [ ] Tauri 壳子搭建，内嵌 Next.js 前端
- [ ] 本地 Python 进程随壳子启动
- [ ] 本地向量库初始化（本地 pgvector 或轻量替代）
- [ ] 云端 RAG + 本地 RAG 路由合并（对 Agent 透明）
- [ ] 本地文件实时索引（监听文件变化，增量入库）

---

## 阶段五：收尾与求职

- [ ] README 完善（架构图、Agent 工作流图、RAG 流程图、本地启动、Docker 启动）
- [ ] 项目难点整理（chunk size 选择依据、JSON 不稳定处理、幻觉降低策略等）
- [ ] 简历项目描述（STAR 法 + 量化指标）
- [ ] 面试讲解稿（3 分钟版本）
- [ ] 高频面试题准备（见 `LEARNING.md`）
- [ ] GitHub 仓库整理（干净、专业、有 Demo 截图）

---

## 时间参考

| 阶段 | 预估时长 | 备注 |
|------|----------|------|
| 阶段一 | 2-3 天 | 优先 Redis + Docker + 异常处理，JWT 最后补 |
| 阶段二 | 1-1.5 周 | RAG 是核心，不要赶 |
| 阶段三 | 1-1.5 周 | 先手写再 LangGraph |
| 阶段四 | 1.5-2 周 | 主项目冲刺；PC 本地端有时间再做 |
| 阶段五 | 3-5 天 | 不要加功能，专注包装 |
