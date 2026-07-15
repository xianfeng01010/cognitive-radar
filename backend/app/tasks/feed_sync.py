import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.feed_sync.sync_feeds")
def sync_feeds():
    logger.info("RSS Feed sync task started")
    logger.info("RSS Feed sync task completed")
    return {"status": "ok"}