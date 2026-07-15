import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.db import get_db
from app.models.history import SearchHistory, ViewHistory, DeleteLog

router = APIRouter()


def _validate_uuid(val: str) -> uuid.UUID:
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"无效的ID: {val}")


@router.get("/")
async def list_history(
    history_type: str = Query("all", pattern="^(all|search|view)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    results = []

    if history_type in ("all", "search"):
        r = await db.execute(
            select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit)
        )
        for row in r.scalars().all():
            results.append({"id": str(row.id), "type": "search", "keyword": row.keyword, "result_count": row.result_count, "strength": row.search_strength, "created_at": row.created_at.isoformat() if row.created_at else None})

    if history_type in ("all", "view"):
        r = await db.execute(
            select(ViewHistory).order_by(ViewHistory.created_at.desc()).limit(limit)
        )
        for row in r.scalars().all():
            results.append({"id": str(row.id), "type": "view", "content_type": row.content_type, "content_title": row.content_title, "url": row.url, "created_at": row.created_at.isoformat() if row.created_at else None})

    results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return {"history": results[:limit], "type": history_type}


# --- Specific routes MUST be above /{history_id} to avoid shadowing ---

@router.delete("/all")
async def delete_all(confirm: bool = Query(False), db: AsyncSession = Depends(get_db)):
    if not confirm:
        raise HTTPException(status_code=400, detail="请传入 confirm=true 确认删除全部历史")

    search_ids = []
    view_ids = []

    r = await db.execute(select(SearchHistory))
    for row in r.scalars().all():
        search_ids.append(str(row.id))
        await db.delete(row)

    r = await db.execute(select(ViewHistory))
    for row in r.scalars().all():
        view_ids.append(str(row.id))
        await db.delete(row)

    db.add(DeleteLog(delete_type="all", deleted_ids={"search": search_ids, "view": view_ids}))
    await db.commit()
    return {"status": "all_deleted", "count": len(search_ids) + len(view_ids)}


@router.delete("/search")
async def delete_all_search(confirm: bool = Query(False), db: AsyncSession = Depends(get_db)):
    if not confirm:
        raise HTTPException(status_code=400, detail="请传入 confirm=true 确认删除全部搜索历史")

    r = await db.execute(select(SearchHistory))
    ids = [str(row.id) for row in r.scalars().all()]
    await db.execute(delete(SearchHistory))

    db.add(DeleteLog(delete_type="search", deleted_ids={"ids": ids}))
    await db.commit()
    return {"status": "deleted", "type": "search", "count": len(ids)}


@router.delete("/view")
async def delete_all_view(confirm: bool = Query(False), db: AsyncSession = Depends(get_db)):
    if not confirm:
        raise HTTPException(status_code=400, detail="请传入 confirm=true 确认删除全部浏览历史")

    r = await db.execute(select(ViewHistory))
    ids = [str(row.id) for row in r.scalars().all()]
    await db.execute(delete(ViewHistory))

    db.add(DeleteLog(delete_type="view", deleted_ids={"ids": ids}))
    await db.commit()
    return {"status": "deleted", "type": "view", "count": len(ids)}


@router.delete("/{history_id}")
async def delete_one(history_id: str, db: AsyncSession = Depends(get_db)):
    uid = _validate_uuid(history_id)
    deleted = False

    r = await db.execute(select(SearchHistory).where(SearchHistory.id == uid))
    row = r.scalar_one_or_none()
    if row:
        await db.delete(row)
        deleted = True
    else:
        r = await db.execute(select(ViewHistory).where(ViewHistory.id == uid))
        row = r.scalar_one_or_none()
        if row:
            await db.delete(row)
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.add(DeleteLog(delete_type="single", deleted_ids={"ids": [history_id]}))
    await db.commit()
    return {"deleted_id": history_id, "status": "deleted"}