# migrations/env.py
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import importlib
import pkgutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.core.database import Base

# Import all models so Alembic can detect them
# Dynamically import every module in app.models to ensure all tables are registered
try:
    import app.models as models_pkg

    for _, module_name, is_pkg in pkgutil.iter_modules(models_pkg.__path__):
        if is_pkg:
            continue
        # skip private modules
        if module_name.startswith("_"):
            continue
        importlib.import_module(f"app.models.{module_name}")
except Exception as e:
    # If dynamic import fails, continue; at worst autogenerate may miss objects
    print(f"[alembic env] Warning: failed to import all models: {e}")

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment or use default
# Note: Alembic uses a sync engine. If the env provides an async URL
# (e.g., postgresql+asyncpg://...), convert it to a sync-compatible URL
# for migrations.
raw_database_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bondhu_db"
)
if raw_database_url.startswith("postgresql+asyncpg"):
    database_url = raw_database_url.replace("postgresql+asyncpg", "postgresql", 1)
else:
    database_url = raw_database_url
config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
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
