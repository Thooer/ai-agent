"""FastAPI application entry point."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from core.config import CORS_ORIGINS, APP_HOST, APP_PORT, LOG_LEVEL
from core.database import get_session
from core.logging import setup_logging
from core.middleware import RequestIdMiddleware
from core.redis_client import get_redis, close_redis
from routers import users, conversations, messages, ai_chat, auth, documents, rag

setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()

    # Ensure pgvector extension exists
    async with get_session() as db:
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await db.commit()

    # Warm up BM25 indexes for all users that have chunks
    from models.orm import Chunk
    from services.bm25_index import rebuild_bm25_index
    async with get_session() as db:
        result = await db.execute(select(Chunk.user_id).distinct())
        user_ids = [row[0] for row in result.fetchall()]

    for uid in user_ids:
        async with get_session() as db:
            await rebuild_bm25_index(db, uid)
    if user_ids:
        logger.info("bm25 warmup complete", extra={"user_count": len(user_ids)})

    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(ai_chat.router)
app.include_router(documents.router)
app.include_router(rag.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    logger.exception("Unhandled exception request_id=%s path=%s", request_id, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
