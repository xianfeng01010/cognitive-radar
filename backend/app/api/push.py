import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_db
from app.models.history import PushHistory, ViewHistory
from app.schemas import PushFeedback

router = APIRouter()


def _validate_uuid(val: str) -> uuid.UUID:
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"无效的ID: {val}")


@router.get("/")
async def list_pushes(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    count_result = await db.execute(select(func.count(PushHistory.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(PushHistory).order_by(PushHistory.created_at.desc()).limit(limit).offset(offset)
    )
    pushes = result.scalars().all()
    return {"pushes": [{"id": str(p.id), "push_tier": p.push_tier, "content_snapshot": p.content_snapshot, "trust_score_at_push": p.trust_score_at_push, "user_feedback": p.user_feedback, "created_at": p.created_at.isoformat() if p.created_at else None} for p in pushes], "total": total}


@router.get("/{push_id}")
async def get_push(push_id: str, db: AsyncSession = Depends(get_db)):
    uid = _validate_uuid(push_id)
    result = await db.execute(select(PushHistory).where(PushHistory.id == uid))
    push = result.scalar_one_or_none()
    if not push:
        raise HTTPException(status_code=404, detail="推送不存在")

    snapshot = push.content_snapshot or {}
    view = ViewHistory(
        content_type="push",
        content_id=push.id,
        content_title=snapshot.get("title", ""),
        source="push",
    )
    db.add(view)
    await db.commit()

    return {"id": str(push.id), "push_tier": push.push_tier, "content_snapshot": snapshot, "trust_score_at_push": push.trust_score_at_push, "user_feedback": push.user_feedback, "created_at": push.created_at.isoformat() if push.created_at else None}


@router.post("/{push_id}/feedback")
async def push_feedback(push_id: str, req: PushFeedback, db: AsyncSession = Depends(get_db)):
    if req.feedback not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="feedback must be 'like' or 'dislike'")

    uid = _validate_uuid(push_id)
    result = await db.execute(select(PushHistory).where(PushHistory.id == uid))
    push = result.scalar_one_or_none()
    if not push:
        raise HTTPException(status_code=404, detail="推送不存在")

    push.user_feedback = req.feedback
    await db.commit()
    return {"status": "recorded", "push_id": push_id, "feedback": req.feedback}