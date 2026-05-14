"""Document management routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.orm import Document, User
from schemas.dto import DocumentResponse, UploadResponse
from services.ingestion import run_ingestion
from services.task_state import create_task, get_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

SUPPORTED_TYPES = {"text/plain": "txt", "text/markdown": "markdown", "application/pdf": "pdf"}
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20MB


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content_type = file.content_type or ""
    # Accept markdown by extension too
    if file.filename and file.filename.endswith(".md"):
        content_type = "text/markdown"

    file_type = SUPPORTED_TYPES.get(content_type)
    if not file_type:
        raise HTTPException(status_code=422, detail=f"Unsupported file type: {content_type}")

    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit")

    # Decode text (PDF handled in parser; for now treat PDF as unsupported until step 4)
    if file_type == "pdf":
        raise HTTPException(status_code=422, detail="PDF support coming soon (step 4)")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("gbk", errors="replace")

    doc = Document(user_id=current_user.id, name=file.filename or "untitled", file_type=file_type)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    task_id = await create_task()
    background_tasks.add_task(run_ingestion, doc.id, text, current_user.id, task_id)

    logger.info("ingestion started", extra={"doc_id": str(doc.id), "task_id": task_id, "user_id": str(current_user.id)})
    return UploadResponse(doc_id=doc.id, task_id=task_id, message="ingestion started")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()

    from services.bm25_index import rebuild_bm25_index
    from core.database import get_session
    async with get_session() as s:
        await rebuild_bm25_index(s, current_user.id)


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
