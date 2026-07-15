from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
async def list_history(history_type: str = Query("all", regex="^(all|search|view)$"), limit: int = 10):
    return {"history": [], "type": history_type, "limit": limit, "message": "流量历史开发中"}


@router.delete("/{history_id}")
async def delete_one(history_id: str):
    return {"deleted_id": history_id, "status": "deleted", "message": "删除单条开发中"}


@router.delete("/all")
async def delete_all(confirm: bool = Query(False)):
    if not confirm:
        return {"error": "需要确认", "message": "请传入 confirm=true 确认删除全部历史"}
    return {"status": "all_deleted", "message": "全部历史已删除（开发中）"}


@router.delete("/search")
async def delete_all_search():
    return {"status": "deleted", "type": "search", "message": "搜索历史已删除（开发中）"}


@router.delete("/view")
async def delete_all_view():
    return {"status": "deleted", "type": "view", "message": "浏览历史已删除（开发中）"}