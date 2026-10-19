from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminInvoice, AdminLedger, AdminRevenueSummary
from app.repositories.base import BaseRepository


class AdminLedgerRepository(BaseRepository[AdminLedger]):
    model = AdminLedger

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_payment(self, crm_payment_id: UUID) -> Optional[AdminLedger]:
        stmt = select(AdminLedger).where(
            AdminLedger.crm_payment_id == crm_payment_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def all_entries(self) -> list[AdminLedger]:
        stmt = select(AdminLedger)
        return list((await self.session.execute(stmt)).scalars().all())

    async def totals_range(
        self, start: date, end: date, currency: str
    ) -> dict[str, Decimal | int]:
        stmt = (
            select(
                AdminLedger.status,
                func.count(),
                func.coalesce(func.sum(AdminLedger.amount), 0),
            )
            .where(
                AdminLedger.currency == currency,
                func.date(AdminLedger.synced_at) >= start,
                func.date(AdminLedger.synced_at) <= end,
            )
            .group_by(AdminLedger.status)
        )
        rows = (await self.session.execute(stmt)).all()
        result: dict[str, Decimal | int] = {
            "total_amount": Decimal("0.00"),
            "transaction_count": 0,
            "completed_count": 0,
            "failed_count": 0,
            "refunded_count": 0,
        }
        for status, count, total in rows:
            count = int(count)
            total = Decimal(str(total or 0))
            result["transaction_count"] = int(result["transaction_count"]) + count
            if status in ("completed", "partial"):
                result["total_amount"] = Decimal(result["total_amount"]) + total
            if status == "completed":
                result["completed_count"] = int(result["completed_count"]) + count
            elif status == "failed":
                result["failed_count"] = int(result["failed_count"]) + count
            elif status == "refunded":
                result["refunded_count"] = int(result["refunded_count"]) + count
        return result


class AdminInvoiceRepository(BaseRepository[AdminInvoice]):
    model = AdminInvoice

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_ledger(self, ledger_id: UUID) -> Optional[AdminInvoice]:
        stmt = select(AdminInvoice).where(AdminInvoice.ledger_id == ledger_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_number(
        self, invoice_number: str
    ) -> Optional[AdminInvoice]:
        stmt = select(AdminInvoice).where(
            AdminInvoice.invoice_number == invoice_number
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_all(self) -> list[AdminInvoice]:
        stmt = select(AdminInvoice).order_by(AdminInvoice.created_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())


class AdminRevenueSummaryRepository(BaseRepository[AdminRevenueSummary]):
    model = AdminRevenueSummary

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_entry(
        self, summary_date: date, period_type: str, currency: str
    ) -> Optional[AdminRevenueSummary]:
        stmt = select(AdminRevenueSummary).where(
            AdminRevenueSummary.summary_date == summary_date,
            AdminRevenueSummary.period_type == period_type,
            AdminRevenueSummary.currency == currency,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_recent(self, limit: int = 30) -> list[AdminRevenueSummary]:
        stmt = (
            select(AdminRevenueSummary)
            .order_by(
                AdminRevenueSummary.summary_date.desc(),
                AdminRevenueSummary.period_type.asc(),
            )
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())
