from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.client import Client
from app.models.visa import Visa, VisaStatus
from app.services.email import send_email


async def collect_reminders(
    session: AsyncSession, *, within_days: int | None = None
) -> dict[str, list[dict[str, Any]]]:
    days = within_days or settings.REMINDER_DAYS
    today = date.today()
    soon = today + timedelta(days=days)

    passport_stmt = select(Client).where(
        Client.is_deleted.is_(False),
        Client.passport_expiry_date.is_not(None),
        Client.passport_expiry_date <= soon,
        Client.passport_expiry_date >= today,
    )
    passports = (await session.execute(passport_stmt)).scalars().all()

    visa_stmt = select(Visa).where(
        Visa.status == VisaStatus.approved.value,
        Visa.expiry_date.is_not(None),
        Visa.expiry_date <= soon,
        Visa.expiry_date >= today,
    )
    visas = (await session.execute(visa_stmt)).scalars().all()

    return {
        "passports": [
            {
                "client_id": str(c.id),
                "client_name": c.full_name,
                "expiry_date": c.passport_expiry_date.isoformat()
                if c.passport_expiry_date
                else None,
            }
            for c in passports
        ],
        "visas": [
            {
                "visa_id": str(v.id),
                "destination_country": v.destination_country,
                "expiry_date": v.expiry_date.isoformat() if v.expiry_date else None,
            }
            for v in visas
        ],
    }


async def run_reminders(session: AsyncSession) -> dict[str, Any]:
    data = await collect_reminders(session)
    passports = data["passports"]
    visas = data["visas"]
    total = len(passports) + len(visas)

    lines: list[str] = []
    for item in passports:
        lines.append(
            f"Passport expiring: {item['client_name']} on {item['expiry_date']}"
        )
    for item in visas:
        lines.append(
            f"Visa expiring: {item['destination_country']} on {item['expiry_date']}"
        )
    body = "\n".join(lines) if lines else "No upcoming expiries."

    sent = False
    if total:
        sent = send_email(
            to=settings.REMINDER_EMAIL,
            subject=f"Travel System reminders ({total})",
            body=body,
        )

    return {"passports": len(passports), "visas": len(visas), "sent": sent}
