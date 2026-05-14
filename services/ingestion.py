"""Ingestion pipeline: text → chunks → embeddings → pgvector."""

import logging
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from models.orm import Chunk, Document
from services.bm25_index import rebuild_bm25_index
from services.chunker import chunk_text
from services.embedding_service import embed_batch
from services.task_state import complete_task, fail_task, update_task_progress

logger = logging.getLogger(__name__)


async def run_ingestion(doc_id: UUID, text: str, user_id: UUID, task_id: str) -> None:
    """Full pipeline: text → chunks → embeddings → DB. Runs as background task."""
    try:
        await _run(doc_id, text, user_id, task_id)
    except Exception as e:
        logger.exception("ingestion failed", extra={"doc_id": str(doc_id), "task_id": task_id})
        await fail_task(task_id, str(e))


async def _run(doc_id: UUID, text: str, user_id: UUID, task_id: str) -> None:
    # Step 1: chunk
    await update_task_progress(task_id, 10)
    chunks = chunk_text(text)
    logger.info("chunked", extra={"doc_id": str(doc_id), "chunk_count": len(chunks)})

    if not chunks:
        await fail_task(task_id, "No chunks produced from document")
        return

    await update_task_progress(task_id, 20)

    # Step 2: embed in batches
    texts = [c.content for c in chunks]
    total_batches = max(1, len(texts) // 32 + (1 if len(texts) % 32 else 0))

    from core.config import EMBEDDING_BATCH_SIZE
    embeddings: list[list[float]] = []
    for batch_idx, start in enumerate(range(0, len(texts), EMBEDDING_BATCH_SIZE)):
        batch_texts = texts[start: start + EMBEDDING_BATCH_SIZE]
        batch_vectors = await embed_batch(batch_texts)
        embeddings.extend(batch_vectors)
        progress = 20 + int((batch_idx + 1) / total_batches * 70)
        await update_task_progress(task_id, progress)
        logger.info("batch embedded", extra={
            "doc_id": str(doc_id), "batch": batch_idx + 1, "total": total_batches
        })

    # Step 3: insert chunks into DB (single transaction)
    async with get_session() as db:
        chunk_orm_list = [
            Chunk(
                user_id=user_id,
                doc_id=doc_id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding=embeddings[i],
                start_char=c.start_char,
                end_char=c.end_char,
            )
            for i, c in enumerate(chunks)
        ]
        db.add_all(chunk_orm_list)

        # Update document chunk_count
        await db.execute(
            update(Document).where(Document.id == doc_id).values(chunk_count=len(chunks))
        )
        await db.commit()

    logger.info("ingestion complete", extra={"doc_id": str(doc_id), "chunks": len(chunks)})
    await update_task_progress(task_id, 95)

    # Step 4: rebuild BM25 index
    async with get_session() as db:
        await rebuild_bm25_index(db, user_id)

    await complete_task(task_id)
    logger.info("task complete", extra={"task_id": task_id})
