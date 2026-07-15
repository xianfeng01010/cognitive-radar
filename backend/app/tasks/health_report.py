import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def _generate_health_report():
    from app.db import create_celery_engine
    from app.models.history import HealthReport, PushHistory, SearchHistory, ViewHistory
    from app.models.source import Source
    from app.models.buffer import BufferItem
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    eng = create_celery_engine()
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        week_ago = datetime.utcnow() - timedelta(days=7)

        total_sources = await db.scalar(
            select(func.count(Source.id)).where(Source.status == "active")
        )
        l1_count = await db.scalar(
            select(func.count(Source.id)).where(Source.cache_level == "L1")
        )
        l2_count = await db.scalar(
            select(func.count(Source.id)).where(Source.cache_level == "L2")
        )
        expired_count = await db.scalar(
            select(func.count(Source.id)).where(Source.status == "expired")
        )

        weekly_pushes = await db.scalar(
            select(func.count(PushHistory.id)).where(PushHistory.created_at >= week_ago)
        )
        weekly_searches = await db.scalar(
            select(func.count(SearchHistory.id)).where(SearchHistory.created_at >= week_ago)
        )
        weekly_views = await db.scalar(
            select(func.count(ViewHistory.id)).where(ViewHistory.created_at >= week_ago)
        )
        pending_buffer = await db.scalar(
            select(func.count(BufferItem.id)).where(BufferItem.status == "pending")
        )
        verified_buffer = await db.scalar(
            select(func.count(BufferItem.id)).where(BufferItem.status == "verified")
        )

        like_count = await db.scalar(
            select(func.count(PushHistory.id)).where(
                PushHistory.user_feedback == "like",
                PushHistory.created_at >= week_ago,
            )
        )
        dislike_count = await db.scalar(
            select(func.count(PushHistory.id)).where(
                PushHistory.user_feedback == "dislike",
                PushHistory.created_at >= week_ago,
            )
        )

        report_data = {
            "period": "weekly",
            "generated_at": datetime.utcnow().isoformat(),
            "sources": {
                "total_active": total_sources or 0,
                "l1_core": l1_count or 0,
                "l2_candidate": l2_count or 0,
                "expired": expired_count or 0,
            },
            "buffer": {
                "pending": pending_buffer or 0,
                "verified": verified_buffer or 0,
            },
            "activity": {
                "weekly_pushes": weekly_pushes or 0,
                "weekly_searches": weekly_searches or 0,
                "weekly_views": weekly_views or 0,
            },
            "feedback": {
                "likes": like_count or 0,
                "dislikes": dislike_count or 0,
            },
        }

        hr = HealthReport(report_data=report_data)
        db.add(hr)
        await db.commit()

    await eng.dispose()
    logger.info("Health report generated")
    return report_data


from app.celery_app import celery_app

@celery_app.task(name="app.tasks.health_report.generate_health_report")
def generate_health_report():
    return asyncio.run(_generate_health_report())