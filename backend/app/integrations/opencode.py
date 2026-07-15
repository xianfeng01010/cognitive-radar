import time
import json
import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, dict] = {
    "opencode": {
        "base_url": "https://opencode.ai/zen/v1",
        "api_key": settings.LLM_API_KEY,
        "model": settings.LLM_MODEL,
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": settings.VOLC_API_KEY,
        "model": settings.VOLC_MODEL_ENDPOINT,
    },
}

_current_provider: str = settings.LLM_PROVIDER if settings.LLM_PROVIDER in _PROVIDERS else "opencode"
_clients: dict[str, AsyncOpenAI] = {}


def _get_client(provider: str) -> AsyncOpenAI:
    if provider not in _clients:
        cfg = _PROVIDERS[provider]
        _clients[provider] = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    return _clients[provider]


def get_provider() -> str:
    return _current_provider


def set_provider(name: str) -> None:
    global _current_provider
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name}")
    if not _PROVIDERS[name]["api_key"]:
        raise ValueError(f"Provider '{name}' has no API key configured")
    _current_provider = name


def get_available_providers() -> list[dict]:
    result = []
    for name, cfg in _PROVIDERS.items():
        result.append({
            "name": name,
            "model": cfg["model"],
            "available": bool(cfg["api_key"]),
            "is_current": name == _current_provider,
        })
    return result


async def llm_complete(
    prompt: str,
    system: str = "",
    model: str = "",
    max_tokens: int = 2000,
    temperature: float = 0.3,
    task_type: str = "unknown",
    db: AsyncSession | None = None,
) -> str:
    provider = _current_provider
    cfg = _PROVIDERS[provider]
    client = _get_client(provider)
    used_model = model or cfg["model"]

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.time()
    success = True
    error_msg = None
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    try:
        response = await client.chat.completions.create(
            model=used_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
        return response.choices[0].message.content
    except Exception as e:
        success = False
        error_msg = str(e)
        raise
    finally:
        latency_ms = int((time.time() - start) * 1000)
        if db:
            try:
                from app.models.ai_usage import AiUsage
                usage = AiUsage(
                    provider=provider,
                    model=used_model,
                    task_type=task_type,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    success=success,
                    error=error_msg,
                )
                db.add(usage)
                await db.commit()
            except Exception as e:
                logger.warning(f"Failed to log AI usage: {e}")


async def llm_json(
    prompt: str,
    system: str = "",
    model: str = "",
    max_tokens: int = 2000,
    task_type: str = "unknown",
    db: AsyncSession | None = None,
) -> dict:
    raw = await llm_complete(prompt, system, model, max_tokens, temperature=0.1, task_type=task_type, db=db)
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) > 1:
            raw = parts[1].strip()
            if raw[:4].lower() == "json":
                raw = raw[4:].strip()
    return json.loads(raw)


async def get_embedding(text: str, model: str = "") -> list[float]:
    client = _get_client("opencode")
    response = await client.embeddings.create(
        model=model or settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
