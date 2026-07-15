from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import search, sources, push, health, history
from app.config import settings

app = FastAPI(
    title="Cognitive Radar API",
    description="Search-driven self-growing information network",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(push.router, prefix="/api/push", tags=["push"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(history.router, prefix="/api/history", tags=["history"])


@app.get("/")
async def root():
    return {
        "name": "Cognitive Radar API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "llm_model": settings.LLM_MODEL,
        "status": "running",
    }


@app.get("/api/health/llm")
async def llm_health():
    from app.integrations.opencode import llm_client
    try:
        response = await llm_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return {"status": "healthy", "model": settings.LLM_MODEL, "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}