from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db import get_db
from app.models.ai_usage import AiUsage

router = APIRouter()


@router.get("/")
async def list_ai_usage(
    provider: str | None = None,
    task_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AiUsage).order_by(desc(AiUsage.created_at)).limit(limit).offset(offset)

    count_stmt = select(func.count(AiUsage.id))

    if provider:
        stmt = stmt.where(AiUsage.provider == provider)
        count_stmt = count_stmt.where(AiUsage.provider == provider)
    if task_type:
        stmt = stmt.where(AiUsage.task_type == task_type)
        count_stmt = count_stmt.where(AiUsage.task_type == task_type)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    return {
        "items": [
            {
                "id": str(r.id),
                "provider": r.provider,
                "model": r.model,
                "task_type": r.task_type,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "error": r.error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def ai_usage_stats(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count(AiUsage.id)))
    total_calls = total_result.scalar() or 0

    tokens_result = await db.execute(
        select(func.sum(AiUsage.total_tokens))
    )
    total_tokens = tokens_result.scalar() or 0

    provider_result = await db.execute(
        select(AiUsage.provider, func.count(AiUsage.id), func.sum(AiUsage.total_tokens))
        .group_by(AiUsage.provider)
    )
    by_provider = [
        {"provider": row[0], "calls": row[1], "tokens": row[2] or 0}
        for row in provider_result
    ]

    task_result = await db.execute(
        select(AiUsage.task_type, func.count(AiUsage.id), func.sum(AiUsage.total_tokens))
        .group_by(AiUsage.task_type)
    )
    by_task = [
        {"task_type": row[0], "calls": row[1], "tokens": row[2] or 0}
        for row in task_result
    ]

    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "by_provider": by_provider,
        "by_task": by_task,
    }
