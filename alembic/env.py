from logging.config import fileConfig
import os
import re

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all ORM models so autogenerate can detect them
from models.orm import Base  # noqa: F401 — side effect: registers all models
target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    # asyncpg driver can't be used by Alembic; swap to psycopg2
    return re.sub(r"postgresql\+asyncpg://", "postgresql://", url)


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
