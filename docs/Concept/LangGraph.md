LangGraph

LangGraph 是 LangChain 团队推出的 Agent 编排框架，核心思想是用有向图（节点 + 边）来定义 Agent 的执行流程。它强调 durable execution（持久化执行，中断后可恢复）、streaming（流式输出）、human-in-the-loop（人工介入审批）等工程化能力，适合构建复杂的多步骤、有条件分支的 Agent 工作流。

大白话：LangGraph 就是用画流程图的方式来编排 Agent 该怎么一步步干活，还能暂停让人审核。
