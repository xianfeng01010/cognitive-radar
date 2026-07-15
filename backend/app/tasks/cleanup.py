import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def _run_cleanup():
    from app.db import create_celery_engine
    from app.models.source import Source
    from app.models.buffer import BufferItem
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    eng = create_celery_engine()
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    expired_sources = 0
    degraded_sources = 0
    expired_buffers = 0

    async with session_factory() as db:
        cutoff_60d = datetime.utcnow() - timedelta(days=60)
        result = await db.execute(
            select(Source).where(
                Source.cache_level == "L2",
                Source.status == "active",
            )
        )
        for source in result.scalars().all():
            if source.last_hit_at and source.last_hit_at < cutoff_60d:
                source.status = "expired"
                source.expires_at = datetime.utcnow()
                expired_sources += 1
            elif not source.last_hit_at and source.added_at < cutoff_60d:
                source.status = "expired"
                source.expires_at = datetime.utcnow()
                expired_sources += 1

        cutoff_30d = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(Source).where(
                Source.cache_level == "L1",
                Source.status == "active",
            )
        )
        for source in result.scalars().all():
            if source.last_hit_at and source.last_hit_at < cutoff_30d:
                source.trust_score = max(source.trust_score - 5.0, 0.0)
                degraded_sources += 1

        result = await db.execute(
            select(BufferItem).where(
                BufferItem.expires_at.is_not(None),
                BufferItem.expires_at < datetime.utcnow(),
                BufferItem.status.in_(["pending", "verified"]),
            )
        )
        for item in result.scalars().all():
            item.status = "expired"
            expired_buffers += 1

        await db.commit()

    await eng.dispose()
    logger.info(f"Cleanup done: {expired_sources} sources expired, {degraded_sources} degraded, {expired_buffers} buffers expired")
    return {"expired_sources": expired_sources, "degraded_sources": degraded_sources, "expired_buffers": expired_buffers}


from app.celery_app import celery_app

@celery_app.task(name="app.tasks.cleanup.run_cleanup")
def run_cleanup():
    return asyncio.run(_run_cleanup())