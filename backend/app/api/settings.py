from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integrations.opencode import get_provider, set_provider, get_available_providers

router = APIRouter()


class ProviderOut(BaseModel):
    name: str
    model: str
    available: bool
    is_current: bool


class ProviderSwitchRequest(BaseModel):
    provider: str


@router.get("/llm-provider")
async def get_llm_provider():
    return {
        "current": get_provider(),
        "providers": get_available_providers(),
    }


@router.post("/llm-provider")
async def switch_llm_provider(req: ProviderSwitchRequest):
    try:
        set_provider(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "current": get_provider(),
        "providers": get_available_providers(),
    }
