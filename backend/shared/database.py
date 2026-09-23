# backend/shared/database.py

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
import logging

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)


@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """Set search path on connect for PostgreSQL"""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET search_path TO public")
    except Exception as e:
        logger.warning(f"Could not set search path: {e}")
    finally:
        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class DatabaseSession:
    """Database session wrapper with context manager support"""

    def __init__(self):
        self._session: Optional[Session] = None

    def __enter__(self) -> Session:
        self._session = SessionLocal()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            if exc_type is not None:
                self._session.rollback()
            self._session.close()

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Database session not initialized. Use 'async with' context.")
        return self._session


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database tables"""
    from shared.models import (
        ReturnRequest, ReturnItem, Alert, TrackingEvent,
        DropOffPoint, BatchUploadRecord
    )

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections"""
    engine.dispose()
    logger.info("Database connections closed")
