from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging

from app.db import get_db
from app.models.source import Source
from app.integrations.rss.factory import create_rss_engine
from app.schemas import SourceCreate, SourceUpdate, SourceOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_sources(cache_level: str = None, status: str = None, db: AsyncSession = Depends(get_db)):
    q = select(Source).order_by(Source.added_at.desc())
    if cache_level:
        q = q.where(Source.cache_level == cache_level)
    if status:
        q = q.where(Source.status == status)
    result = await db.execute(q)
    sources = result.scalars().all()
    return {"sources": [{"id": str(s.id), "name": s.name, "url": s.url, "source_type": s.source_type, "cache_level": s.cache_level, "trust_score": s.trust_score, "status": s.status, "hit_count": s.hit_count, "last_hit_at": s.last_hit_at.isoformat() if s.last_hit_at else None, "added_at": s.added_at.isoformat() if s.added_at else None} for s in sources]}


@router.post("/")
async def add_source(req: SourceCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Source).where(Source.url == req.url))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该URL已存在")

    miniflux_feed_id = None
    if req.source_type == "R":
        try:
            rss_engine = create_rss_engine()
            miniflux_feed_id = await rss_engine.add_feed(req.url)
        except Exception as e:
            logger.error(f"Failed to add feed to Miniflux: {e}")
            raise HTTPException(status_code=502, detail=f"RSS订阅失败: {e}")

    source = Source(
        name=req.name or req.url[:255],
        url=req.url,
        source_type=req.source_type,
        cache_level=req.cache_level,
        refresh_interval_sec=req.refresh_interval_sec,
        miniflux_feed_id=miniflux_feed_id,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return {"id": str(source.id), "name": source.name, "url": source.url, "miniflux_feed_id": miniflux_feed_id}


@router.get("/{source_id}")
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    return {"id": str(source.id), "name": source.name, "url": source.url, "source_type": source.source_type, "cache_level": source.cache_level, "trust_score": source.trust_score, "status": source.status, "hit_count": source.hit_count, "miniflux_feed_id": source.miniflux_feed_id, "refresh_interval_sec": source.refresh_interval_sec, "last_hit_at": source.last_hit_at.isoformat() if source.last_hit_at else None, "added_at": source.added_at.isoformat() if source.added_at else None, "expires_at": source.expires_at.isoformat() if source.expires_at else None}


@router.put("/{source_id}")
async def update_source(source_id: str, req: SourceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")

    if req.name is not None:
        source.name = req.name
    if req.status is not None:
        source.status = req.status
    if req.refresh_interval_sec is not None:
        source.refresh_interval_sec = req.refresh_interval_sec
        if source.miniflux_feed_id and source.source_type == "R":
            try:
                rss_engine = create_rss_engine()
                await rss_engine.update_feed(source.miniflux_feed_id, refresh_interval=req.refresh_interval_sec)
            except Exception as e:
                logger.warning(f"Failed to update Miniflux feed: {e}")
    if req.cache_level is not None:
        source.cache_level = req.cache_level

    await db.commit()
    return {"status": "updated", "id": str(source.id)}


@router.delete("/{source_id}")
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")

    if source.miniflux_feed_id and source.source_type == "R":
        try:
            rss_engine = create_rss_engine()
            await rss_engine.remove_feed(source.miniflux_feed_id)
        except Exception as e:
            logger.warning(f"Failed to remove feed from Miniflux: {e}")

    await db.delete(source)
    await db.commit()
    return {"status": "deleted", "id": source_id}