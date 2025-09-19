import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from tenacity import retry, stop_after_attempt, wait_exponential
from db.models import Base
from .config import settings
from typing import Generator, AsyncGenerator
from loguru import logger
import time

def create_sync_engine():
    """Create synchronous engine with connection pooling and monitoring"""
    engine = create_engine(
        settings.DATABASE_URL,
        future=True,
        poolclass=QueuePool,
        pool_size=20,  # Max number of connections in the pool
        max_overflow=10,  # Allow up to 10 additional connections
        pool_timeout=30,  # Wait up to 30 seconds for available connection
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True,  # Check connection health before using
    )

    # Add event listeners for monitoring
    @event.listens_for(engine, 'checkout')
    def checkout(dbapi_conn, connection_record, connection_proxy):
        """Log slow checkouts and mark connection start time"""
        connection_record.info['checkout_started'] = time.time()

    @event.listens_for(engine, 'checkin')
    def checkin(dbapi_conn, connection_record):
        """Log slow connections"""
        checkout_started = connection_record.info.get('checkout_started')
        if checkout_started is not None:
            total_time = time.time() - checkout_started
            if total_time > 1:  # Log if connection was held more than 1 second
                logger.warning(f"Slow database connection: {total_time:.2f}s")

    return engine

# Create synchronous engine (used for migrations and simple ops)
engine = create_sync_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Create async engine only when using PostgreSQL (asyncpg)
async_engine = None
AsyncSessionLocal = None
if settings.DATABASE_URL.startswith("postgresql://"):
    async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    async_engine = create_async_engine(
        async_url,
        echo=settings.DEBUG,
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True
    )


def create_tables() -> None:
    """Create all tables synchronously using the sync engine."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
def get_db() -> Generator:
    """Sync DB session generator with retry logic (FastAPI dependency compatible)."""
    db = SessionLocal()
    try:
        # Test connection before returning
        db.execute(text("SELECT 1"))
        yield db
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        db.rollback()
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async DB session generator with enhanced error handling.
    
    Raises:
        RuntimeError: if async engine is not configured
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Async DB is not configured for the current DATABASE_URL")

    try:
        async with AsyncSessionLocal() as session:
            # Test connection
            await session.execute(text("SELECT 1"))
            yield session
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()


def test_db_connection() -> bool:
    """Test database connection synchronously."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def test_async_db_connection() -> bool:
    """Test async database connection."""
    if async_engine is None:
        return True  # Skip if not configured
    
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            logger.info("Async database connection successful")
            return True
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        return False