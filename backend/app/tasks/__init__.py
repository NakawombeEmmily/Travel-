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
