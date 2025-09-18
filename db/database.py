import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .models import Base
from dotenv import load_dotenv
from typing import Generator, AsyncGenerator

load_dotenv()

# Read DB URL from env; if missing use a local sqlite file for easy development.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./dev.db"

# Create synchronous engine (used for migrations and simple ops)
engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Create async engine only when using PostgreSQL (asyncpg)
async_engine = None
AsyncSessionLocal = None
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    async_url = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    async_engine = create_async_engine(async_url, echo=True, future=True)
    AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False, future=True)


def create_tables() -> None:
    """Create all tables synchronously using the sync engine."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    """Sync DB session generator (FastAPI dependency compatible)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator:
    """Async DB session generator (FastAPI dependency). Only available when using PostgreSQL+asyncpg.

    Raises:
        RuntimeError: if async engine is not configured.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Async DB is not configured for the current DATABASE_URL")

    async with AsyncSessionLocal() as session:
        yield session