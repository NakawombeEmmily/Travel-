from __future__ import annotations

import asyncio
from typing import Any

from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="tasks.send_reminders")
def send_reminders() -> dict[str, Any]:
    return asyncio.run(_send_reminders())


async def _send_reminders() -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.reminders import run_reminders

    async with SessionLocal() as session:
        result = await run_reminders(session)
        await session.commit()
        return result


@celery_app.task(name="tasks.process_outbox")
def process_outbox(limit: int = 100) -> dict[str, Any]:
    return asyncio.run(_process_outbox(limit))


async def _process_outbox(limit: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.outbox import OutboxService

    async with SessionLocal() as session:
        return await OutboxService(session).process_pending(limit=limit)


@celery_app.task(name="tasks.reconcile_payments")
def reconcile_payments() -> dict[str, Any]:
    return asyncio.run(_reconcile_payments())


async def _reconcile_payments() -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.reconciliation import ReconciliationService

    async with SessionLocal() as session:
        result = await ReconciliationService(session).reconcile()
        await session.commit()
        return result.model_dump()
