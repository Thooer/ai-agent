"""Build RAG context string from retrieved chunks."""

from services.hybrid_search import RetrievedChunk


def build_rag_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""

    parts = ["以下是相关参考内容，请据此回答用户问题。如参考内容不足，请直接说明，不要编造。\n\n=== 参考内容 ==="]
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[{i}] 来自《{c.doc_name}》第 {c.chunk_index + 1} 段：\n{c.content}")
    parts.append("=================\n")
    return "\n\n".join(parts)
