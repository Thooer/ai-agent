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
