from __future__ import annotations

import csv
import io
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.feedback import Feedback
from app.models.lead import Lead
from app.models.payment import Payment
from app.models.trip import Trip
from app.models.visa import Visa
from app.services.exceptions import NotFoundError

CSV_DATASETS = ("clients", "trips", "visas", "leads", "feedback", "payments")


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def rows_to_csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_stringify(cell) for cell in row])
    return buffer.getvalue().encode("utf-8-sig")


async def _clients(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    rows = (
        await session.execute(
            select(Client)
            .where(Client.is_deleted.is_(False))
            .order_by(Client.created_at.desc())
        )
    ).scalars().all()
    headers = [
        "id",
        "full_name",
        "email",
        "phone",
        "nationality",
        "passport_expiry_date",
        "consent_given",
        "created_at",
    ]
    data = [
        [
            c.id,
            c.full_name,
            c.email,
            c.phone,
            c.nationality,
            c.passport_expiry_date,
            c.consent_given,
            c.created_at,
        ]
        for c in rows
    ]
    return headers, data


async def _trips(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    result = await session.execute(
        select(Trip, Client.full_name)
        .join(Client, Trip.client_id == Client.id)
        .order_by(Trip.created_at.desc())
    )
    headers = [
        "id",
        "client_name",
        "destination_country",
        "travel_start_date",
        "travel_end_date",
        "purpose",
        "status",
        "total_cost",
        "currency",
        "created_at",
    ]
    data = [
        [
            t.id,
            name,
            t.destination_country,
            t.travel_start_date,
            t.travel_end_date,
            t.purpose,
            t.status,
            t.total_cost,
            t.currency,
            t.created_at,
        ]
        for t, name in result.all()
    ]
    return headers, data


async def _visas(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    result = await session.execute(
        select(Visa, Client.full_name)
        .join(Client, Visa.client_id == Client.id)
        .order_by(Visa.updated_at.desc())
    )
    headers = [
        "id",
        "client_name",
        "destination_country",
        "visa_type",
        "status",
        "application_date",
        "submission_date",
        "approval_date",
        "expiry_date",
        "reference_number",
    ]
    data = [
        [
            v.id,
            name,
            v.destination_country,
            v.visa_type,
            v.status,
            v.application_date,
            v.submission_date,
            v.approval_date,
            v.expiry_date,
            v.reference_number,
        ]
        for v, name in result.all()
    ]
    return headers, data


async def _leads(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    rows = (
        await session.execute(select(Lead).order_by(Lead.created_at.desc()))
    ).scalars().all()
    headers = [
        "id",
        "full_name",
        "email",
        "phone",
        "source",
        "status",
        "created_at",
    ]
    data = [
        [
            lead.id,
            lead.full_name,
            lead.email,
            lead.phone,
            lead.source,
            lead.status,
            lead.created_at,
        ]
        for lead in rows
    ]
    return headers, data


async def _feedback(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    result = await session.execute(
        select(Feedback, Client.full_name)
        .join(Client, Feedback.client_id == Client.id)
        .order_by(Feedback.feedback_date.desc())
    )
    headers = [
        "id",
        "client_name",
        "rating",
        "sentiment",
        "category",
        "comment",
        "feedback_date",
    ]
    data = [
        [f.id, name, f.rating, f.sentiment, f.category, f.comment, f.feedback_date]
        for f, name in result.all()
    ]
    return headers, data


async def _payments(session: AsyncSession) -> tuple[list[str], list[list[Any]]]:
    result = await session.execute(
        select(Payment, Client.full_name)
        .join(Client, Payment.client_id == Client.id)
        .order_by(Payment.created_at.desc())
    )
    headers = [
        "id",
        "invoice_number",
        "client_name",
        "amount",
        "currency",
        "method",
        "provider",
        "status",
        "paid_at",
        "created_at",
    ]
    data = [
        [
            p.id,
            p.invoice_number,
            name,
            p.amount,
            p.currency,
            p.method,
            p.provider,
            p.status,
            p.paid_at,
            p.created_at,
        ]
        for p, name in result.all()
    ]
    return headers, data


ExportBuilder = Callable[
    [AsyncSession], Awaitable[tuple[list[str], list[list[Any]]]]
]

_EXPORT_BUILDERS: dict[str, ExportBuilder] = {
    "clients": _clients,
    "trips": _trips,
    "visas": _visas,
    "leads": _leads,
    "feedback": _feedback,
    "payments": _payments,
}


async def export_dataset(
    session: AsyncSession, dataset: str
) -> tuple[str, bytes]:
    builder = _EXPORT_BUILDERS.get(dataset)
    if builder is None:
        raise NotFoundError(f"Unknown dataset: {dataset}")
    headers, data = await builder(session)
    filename = f"{dataset}-{date.today().isoformat()}.csv"
    return filename, rows_to_csv(headers, data)
