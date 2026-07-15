import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def _check_and_push():
    from app.db import create_celery_engine
    from app.models.buffer import BufferItem
    from app.models.history import PushHistory
    from app.models.source import Entry, Source
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    eng = create_celery_engine()
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    pushed = 0
    async with session_factory() as db:
        result = await db.execute(
            select(BufferItem)
            .where(
                BufferItem.status == "verified",
                BufferItem.priority_score >= 40.0,
                BufferItem.expires_at.is_(None) | (BufferItem.expires_at > datetime.utcnow()),
            )
            .order_by(BufferItem.priority_score.desc())
            .limit(20)
        )
        items = result.scalars().all()

        for item in items:
            entry_result = await db.execute(
                select(Entry).where(Entry.id == item.entry_id)
            )
            entry = entry_result.scalar_one_or_none()
            if not entry:
                continue

            source_result = await db.execute(
                select(Source).where(Source.id == entry.source_id)
            )
            source = source_result.scalar_one_or_none()
            trust_score = source.trust_score if source else 50.0

            tier = "important" if item.priority_score >= 80 else "normal" if item.priority_score >= 60 else "low"

            push = PushHistory(
                buffer_item_id=item.id,
                push_tier=tier,
                content_snapshot={
                    "entry_id": str(entry.id),
                    "title": entry.title,
                    "url": entry.url,
                    "content_preview": entry.content[:200] if entry.content else "",
                    "source_name": source.name if source else "",
                    "priority_score": item.priority_score,
                },
                trust_score_at_push=trust_score,
            )
            db.add(push)

            item.status = "pushed"
            pushed += 1

        await db.commit()

    await eng.dispose()
    logger.info(f"Push check done: {pushed} items pushed")
    return {"pushed": pushed}


from app.celery_app import celery_app

@celery_app.task(name="app.tasks.push_check.check_and_push")
def check_and_push():
    return asyncio.run(_check_and_push())