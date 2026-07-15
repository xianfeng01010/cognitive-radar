import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def _sync_feeds():
    from app.db import create_celery_engine, celery_session
    from app.models.source import Source, Entry
    from app.integrations.rss.factory import create_rss_engine
    from app.integrations import meilisearch_client as meili
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    eng = create_celery_engine()
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    rss_engine = create_rss_engine()
    synced = 0
    errors = 0

    async with session_factory() as db:
        result = await db.execute(
            select(Source).where(Source.status == "active", Source.source_type == "R")
        )
        sources = result.scalars().all()

        for source in sources:
            try:
                entries = await rss_engine.get_entries(
                    feed_id=source.miniflux_feed_id,
                    since=source.last_hit_at,
                    limit=100,
                )
                for e in entries:
                    existing = await db.execute(
                        select(Entry).where(Entry.content_hash == e.content_hash)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    entry = Entry(
                        source_id=source.id,
                        title=e.title,
                        content=e.content[:10000] if e.content else "",
                        url=e.url,
                        author=e.author,
                        published_at=e.published_at,
                        collected_at=datetime.utcnow(),
                        content_hash=e.content_hash,
                        metadata_=e.metadata,
                    )
                    db.add(entry)
                    await db.flush()

                    doc = {
                        "id": str(entry.id),
                        "title": entry.title,
                        "content": entry.content[:500],
                        "url": entry.url,
                        "source_id": str(source.id),
                        "source_type": source.source_type,
                        "published_at": entry.published_at.isoformat() if entry.published_at else None,
                        "collected_at": entry.collected_at.isoformat() if entry.collected_at else None,
                        "keywords": [],
                    }
                    try:
                        await meili.add_documents(meili.INDEX_ENTRIES, [doc])
                    except Exception as me:
                        logger.warning(f"Meilisearch indexing failed for entry {entry.id}: {me}")

                    source.hit_count += 1
                    source.last_hit_at = datetime.utcnow()
                    synced += 1

                    await rss_engine.mark_read(e.id)

                    await db.commit()
            except Exception as e:
                logger.error(f"Failed to sync source {source.id}: {e}")
                await db.rollback()
                errors += 1

    await eng.dispose()
    logger.info(f"Feed sync done: {synced} new entries, {errors} errors")
    return {"synced": synced, "errors": errors}


from app.celery_app import celery_app

@celery_app.task(name="app.tasks.feed_sync.sync_feeds")
def sync_feeds():
    return asyncio.run(_sync_feeds())