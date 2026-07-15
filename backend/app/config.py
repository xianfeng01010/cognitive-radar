from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://radar:radar_dev_2026@localhost:5432/cognitive_radar"
    REDIS_URL: str = "redis://localhost:6379/0"

    MEILI_URL: str = "http://localhost:7700"
    MEILI_KEY: str = "meili_dev_key_2026"

    MINIFLUX_URL: str = "http://localhost:8080"
    MINIFLUX_USER: str = "admin"
    MINIFLUX_PASSWORD: str = "admin123"

    SEARXNG_URL: str = "http://localhost:8888"

    LLM_BASE_URL: str = "https://opencode.ai/zen/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-v4-flash-free"
    EMBEDDING_MODEL: str = "google/gemini-embedding-001"

    VOLC_API_KEY: str = ""
    VOLC_MODEL_ENDPOINT: str = ""
    LLM_PROVIDER: str = "opencode"

    RSS_ENGINE_TYPE: str = "miniflux"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()