from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import httpx
import redis.asyncio as aioredis

from app.db import get_db, engine
from app.config import settings
from app.models.history import HealthReport
from app.integrations import meilisearch_client as meili
from app.integrations.rss.factory import create_rss_engine
from app.integrations.searxng_client import searxng_client
from app.integrations.opencode import llm_complete

router = APIRouter()


@router.get("/")
async def system_health():
    components = {}

    # PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["postgres"] = "healthy"
    except Exception as e:
        components["postgres"] = f"unhealthy: {e}"

    # Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        components["redis"] = "healthy"
    except Exception as e:
        components["redis"] = f"unhealthy: {e}"

    # Meilisearch
    try:
        m = await meili.health()
        components["meilisearch"] = m["status"]
    except Exception as e:
        components["meilisearch"] = f"unhealthy: {e}"

    # Miniflux
    try:
        rss_engine = create_rss_engine()
        result = await rss_engine.health_check()
        components["miniflux"] = result["status"]
    except Exception as e:
        components["miniflux"] = f"unhealthy: {e}"

    # SearXNG
    try:
        results = await searxng_client.search("test", limit=1)
        components["searxng"] = "healthy"
    except Exception as e:
        components["searxng"] = f"unhealthy: {e}"

    # LLM
    try:
        resp = await llm_complete("ping", max_tokens=5, task_type="health_check", db=db)
        components["llm"] = "healthy"
    except Exception as e:
        components["llm"] = f"unhealthy: {e}"

    all_healthy = all(v == "healthy" for v in components.values())
    return {"status": "healthy" if all_healthy else "degraded", "components": components}


@router.get("/report")
async def get_latest_report(limit: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthReport).order_by(HealthReport.created_at.desc()).limit(limit)
    )
    reports = result.scalars().all()
    return {"reports": [{"id": str(r.id), "report_data": r.report_data, "created_at": r.created_at.isoformat() if r.created_at else None} for r in reports]}