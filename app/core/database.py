# app/core/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
from typing import Generator
import logging
import os


from app.core.config import get_settings

logger = logging.getLogger(__name__)

# When Alembic imports this module during migrations, application settings
# (Pydantic BaseSettings) may not be fully populated and will raise
# ValidationError. To avoid breaking imports, attempt to instantiate settings
# inside a try/except and fall back to environment variables if it fails.
try:
    settings = get_settings()
    DATABASE_URL = settings.database_url
    APP_ENV = settings.app_env
    DEBUG = settings.debug
except Exception:
    # fallback values when Settings can't be instantiated (e.g. during alembic)
    logger.warning(
        "Settings unavailable at import time; falling back to env vars for DB config"
    )
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/bondhu_db",
    )
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# Normalize async driver URL to sync driver for SQLAlchemy sync engine
if isinstance(DATABASE_URL, str) and DATABASE_URL.startswith("postgresql+asyncpg"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)

# Create engine with appropriate pool settings
if APP_ENV == "production":
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=DEBUG,  # Log SQL in debug mode
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Don't expire objects after commit
)

# Base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields db sessions
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# Context manager for db session
@contextmanager
def get_db_session():
    """
    Context manager for database sessions
    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Event listeners for debugging (development only)
if DEBUG:

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.info("Database connection established")

    @event.listens_for(engine, "close")
    def receive_close(dbapi_connection, connection_record):
        logger.info("Database connection closed")


# Database initialization
def init_db():
    """
    Initialize database tables
    """
    # Import all models here to ensure they're registered
    from app.models import (
        user,
        profile,
        student,
        teacher,
        parent,
        admin,
        auth,
        chat_room,
        chat,
        credit,
        document_storage,
        quiz,
        syllabus,
        subscription,
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


# Health check
async def check_database_connection():
    """
    Check if database is accessible
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


# Vector extension setup for PostgreSQL
def setup_vector_extension():
    """
    Setup pgvector extension for vector similarity search
    """
    try:
        with engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        logger.info("pgvector extension setup completed")
    except Exception as e:
        logger.error(f"Failed to setup pgvector: {str(e)}")
        raise
