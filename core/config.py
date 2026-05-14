"""Application configuration."""

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://thooer:thooer123@localhost:5432/ai_agent"
)

BIGMODEL_API_KEY = os.getenv("BIGMODEL_API_KEY", "")
BIGMODEL_BASE_URL = os.getenv(
    "BIGMODEL_BASE_URL",
    "https://open.bigmodel.cn/api/paas/v4"
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PROJECT_PREFIX = os.getenv("REDIS_PROJECT_PREFIX", "ai-agent:dev")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

# RAG
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embedding-3")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", "10"))
BM25_TOP_K = int(os.getenv("BM25_TOP_K", "10"))
RRF_K = int(os.getenv("RRF_K", "60"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "5"))
RAG_RELEVANCE_THRESHOLD = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.3"))
