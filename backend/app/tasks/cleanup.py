import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.run_cleanup")
def run_cleanup():
    logger.info("Cleanup task started")
    logger.info("Cleanup task completed")
    return {"status": "ok"}