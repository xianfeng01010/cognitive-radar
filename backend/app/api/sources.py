from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_sources():
    return {"sources": [], "message": "来源管理开发中"}


@router.get("/{source_id}")
async def get_source(source_id: str):
    return {"source_id": source_id, "message": "来源详情开发中"}