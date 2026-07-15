import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.verification.verify_item")
def verify_item(buffer_item_id: str):
    logger.info(f"Verification task started for {buffer_item_id}")
    return {"status": "ok", "item_id": buffer_item_id}