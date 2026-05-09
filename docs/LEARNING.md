# 学习参考 / 面试准备

> 个人参考手册，不影响项目本身。
> 三份 AI 建议的共识提炼，去掉重复内容。

---

## 技术栈优先级

### 必须学到能讲清楚（面试直接问）

1. FastAPI（路由、Pydantic、StreamingResponse、依赖注入）
2. LLM API 调用（messages 结构、streaming、错误重试、超时处理）
3. Prompt Engineering（角色设定、CoT、few-shot、结构化输出约束）
4. Function Calling / Tool Calling
5. Embedding（向量是什么、相似度检索、top-k）
6. RAG（chunking、hybrid search、引用来源、降低幻觉）
7. LangGraph（State、Node、Edge、Conditional Edge、checkpoint）
8. Docker / Docker Compose
9. PostgreSQL + SQLAlchemy
10. 项目部署（生产环境 gunicorn + uvicorn worker）

### 了解是什么即可（简历广度用）

- LoRA / 微调基础
- CrewAI（多 Agent 协作概念）
- MCP（Model Context Protocol）
- LangSmith / Langfuse（可观测工具）
- vLLM / 模型量化（了解概念）

### 暂时别碰（时间不够）

- 从零训练大模型
- Transformer 数学细节
- CUDA
- 复杂多 Agent 辩论系统
- 花大量时间调前端 UI

---

## 面试高频题

### Agent 相关

- 什么是 AI Agent？和普通 Chatbot 有什么区别？
- ReAct 是什么？怎么实现？
- Tool Calling 的完整流程是什么？
- Agent 为什么容易失控？怎么控制？
- LangGraph 相比 LangChain Chain 的优势是什么？
- Memory 怎么设计？短期 / 长期 / 向量记忆的区别？
- 如何做 human-in-the-loop？
- 多 Agent 有什么问题？什么时候用多 Agent？

### RAG 相关

- RAG 是什么？解决了什么问题？
- 为什么需要 chunk？chunk size 怎么选？
- top-k 怎么选？
- 向量检索为什么会召回错误？怎么改善？
- hybrid search 是什么？BM25 和向量各解决什么问题？
- RRF 融合是什么原理？
- rerank 有什么用？什么时候加？
- RAG 和微调有什么区别？什么时候用哪个？
- 怎么降低幻觉？（引用来源、检索为空拒答、结构化输出校验）
- 怎么评估 RAG 效果？recall@k、MRR、answer faithfulness 是什么？

### 工程相关

- FastAPI 为什么适合 AI 应用？
- SSE 流式响应怎么实现？backpressure 怎么处理？
- LLM 接口超时怎么办？
- LLM 输出 JSON 不稳定怎么处理？
- token 成本怎么控制？
- 如何做限流？
- 如何保护 API key？
- 如果并发上来怎么优化？
- 文件上传 100MB 怎么处理？

### 项目细节（必须能回答，答不出说明项目不够真）

- 你的 chunk size 是多少？为什么？
- top-k 设多少？为什么？
- 向量库里存了哪些字段？
- Agent 状态里有哪些 key？
- 哪一步最容易出错？
- 怎么排查模型幻觉？

---

## 项目讲解模板（3 分钟版）

```
这个项目不是简单套壳聊天机器人，而是一个 [场景] 的 Agent 系统。

用户 [输入什么] 后，系统会：
1. [第一步做什么]
2. [第二步做什么]
3. [第三步做什么]

工程上：
- FastAPI 提供接口，SSE 流式输出
- pgvector 做向量检索，自实现 hybrid search（BM25 + 向量 + RRF 融合）
- LangGraph 编排 Agent 工作流
- Docker Compose 一键部署

为了降低幻觉，我做了：引用来源、结构化输出校验、检索为空拒答、工具调用失败兜底。

RAG recall@5 达到 X%，相比纯向量检索提升了 Y%。
```

---

## 简历项目描述模板

**写法**（具体）：
> 基于 FastAPI + LangGraph + RAG 实现 [项目名]，支持 [功能1]、[功能2]、[功能3]。使用 pgvector 构建向量检索，自实现 BM25 + 向量 hybrid search（RRF 融合），结合 Tool Calling 与 LangGraph 状态机完成多步骤 Agent 工作流，实现流式输出、异常重试、结构化 JSON 校验、Docker Compose 一键部署。RAG recall@5 达到 X%。

**不要写**（虚）：
> 熟悉 AI Agent，熟悉 LangChain，熟悉 RAG。

---

## 项目 README 必须包含

1. 项目简介 + 解决的问题
2. 技术栈
3. 系统架构图
4. Agent 工作流图
5. RAG 流程图
6. 功能演示截图 / 视频
7. 本地启动方式
8. Docker 启动方式
9. 项目难点（这部分最重要）
10. 优化方向

**项目难点可以写**：
- 文档切分对召回质量的影响（chunk size 实验对比）
- LLM 输出 JSON 不稳定的处理策略
- Agent 工具调用链路过长导致错误传播
- 检索结果无关导致幻觉的降低方案
- 多轮对话中的状态管理
- token 成本和响应速度的平衡

---

## 投递关键词

不要只投"AI Agent 工程师"，还要投：

- AI 应用开发实习生 / 应届
- 大模型应用开发工程师
- LLM 应用开发
- RAG 开发工程师
- Python 后端开发（JD 里有 LangChain / RAG 的）
- 智能体平台开发
- 企业知识库开发
- AIGC 应用开发

---

## 避坑清单

- 不要只看课不写代码，每天必须有代码产出
- 不要做"10 个 Agent 自动创业"这种花哨 demo，面试官不吃这个
- 不要以为 Agent 就是多 Agent，初级岗更看重单 Agent + 工具调用 + RAG + 工程部署
- 不要追求完美 UI，卷交互细节和工程闭环
- 卡住立刻问 AI 或查文档，不要死磕超过 30 分钟
- 每天复盘：今天写了什么、明天优化什么

---

## 每天时间分配参考

| 时间 | 内容 |
|------|------|
| 上午 2h | 学习新概念 / 看文档 |
| 下午 3-4h | 项目编码 |
| 晚上 1h | 面试题 / 复盘笔记 |

核心原则：**能跑 > 能演示 > 能讲清楚 > 能部署 > 再谈高级理论**
