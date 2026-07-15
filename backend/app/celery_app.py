from celery import Celery
from app.config import settings

celery_app = Celery(
    "cognitive_radar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.feed_sync", "app.tasks.verification", "app.tasks.push_check", "app.tasks.health_report", "app.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    beat_schedule={
        "sync-rss-feeds": {
            "task": "app.tasks.feed_sync.sync_feeds",
            "schedule": 1800.0,
        },
        "check-pushes": {
            "task": "app.tasks.push_check.check_and_push",
            "schedule": 1800.0,
        },
        "weekly-health-report": {
            "task": "app.tasks.health_report.generate_health_report",
            "schedule": 604800.0,
            "options": {"name": "weekly-health-report"},
        },
        "daily-cleanup": {
            "task": "app.tasks.cleanup.run_cleanup",
            "schedule": 86400.0,
        },
    },
)