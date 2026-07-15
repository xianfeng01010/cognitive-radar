from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings
from app.models.base import Base

engine = create_async_engine(settings.DATABASE_URL, echo=settings.ENVIRONMENT == "development", pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


def create_celery_engine():
    """Create a fresh engine for Celery tasks (avoids stale event loop connections)."""
    return create_async_engine(settings.DATABASE_URL, pool_size=5, max_overflow=10)


def celery_session(eng=None):
    """Create a session from a fresh engine for Celery tasks."""
    if eng is None:
        eng = create_celery_engine()
    return async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)()