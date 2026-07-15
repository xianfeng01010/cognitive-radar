from app.config import settings
from .miniflux_adapter import MinifluxAdapter


def create_rss_engine():
    engine_type = settings.RSS_ENGINE_TYPE
    if engine_type == "miniflux":
        return MinifluxAdapter(
            base_url=settings.MINIFLUX_URL,
            username=settings.MINIFLUX_USER,
            password=settings.MINIFLUX_PASSWORD,
        )
    raise ValueError(f"Unsupported RSS engine type: {engine_type}")