import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.push_check.check_and_push")
def check_and_push():
    logger.info("Push check task started")
    logger.info("Push check task completed")
    return {"status": "ok"}