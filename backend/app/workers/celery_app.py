from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "travel_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # Mirrors the render.yaml crons so local and production schedules match:
        # 09:00 UTC daily reminders, every-5-minute outbox, 02:00 UTC reconciliation.
        "send-reminders-daily": {
            "task": "tasks.send_reminders",
            "schedule": crontab(hour=9, minute=0),
        },
        "process-payment-outbox": {
            "task": "tasks.process_outbox",
            "schedule": 60.0,
        },
        "reconcile-payments-nightly": {
            "task": "tasks.reconcile_payments",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
