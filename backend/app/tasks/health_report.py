import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.health_report.generate_health_report")
def generate_health_report():
    logger.info("Health report generation started")
    return {"status": "ok"}