from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_pushes():
    return {"pushes": [], "message": "推送列表开发中"}


@router.post("/{push_id}/feedback")
async def push_feedback(push_id: str, feedback: str):
    return {"push_id": push_id, "feedback": feedback, "status": "recorded"}