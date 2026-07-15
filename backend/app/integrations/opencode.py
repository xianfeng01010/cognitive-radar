from openai import AsyncOpenAI
from app.config import settings

llm_client = AsyncOpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
)


async def llm_complete(prompt: str, system: str = "", model: str = "", max_tokens: int = 2000, temperature: float = 0.3) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await llm_client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


async def llm_json(prompt: str, system: str = "", model: str = "", max_tokens: int = 2000) -> dict:
    import json
    raw = await llm_complete(prompt, system, model, max_tokens, temperature=0.1)
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) > 1:
            raw = parts[1].strip()
            if raw[:4].lower() == "json":
                raw = raw[4:].strip()
    return json.loads(raw)


async def get_embedding(text: str, model: str = "") -> list[float]:
    response = await llm_client.embeddings.create(
        model=model or settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding