from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def system_health():
    return {
        "status": "ok",
        "components": {
            "postgres": "unknown",
            "redis": "unknown",
            "meilisearch": "unknown",
            "miniflux": "unknown",
            "searxng": "unknown",
            "llm": "unknown",
        },
        "message": "系统健康检查开发中",
    }


@router.get("/report")
async def health_report():
    return {"report": None, "message": "健康报告开发中"}