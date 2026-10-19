from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.payment import (
    OutboxStatus,
    Payment,
    PaymentInstallment,
    PaymentOutbox,
    PaymentStatus,
    InstallmentStatus,
)
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        trip_id: Optional[UUID] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[tuple[Payment, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(Payment.client_id == client_id)
        if trip_id:
            conditions.append(Payment.trip_id == trip_id)
        if status:
            conditions.append(Payment.status == status)
        if provider:
            conditions.append(Payment.provider == provider)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    Payment.invoice_number.ilike(like),
                    Payment.provider_transaction_id.ilike(like),
                    Client.full_name.ilike(like),
                )
            )

        base = select(Payment).join(Client, Payment.client_id == Client.id)
        count_stmt = (
            select(func.count())
            .select_from(Payment)
            .join(Client, Payment.client_id == Client.id)
            .where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            base.where(*conditions)
            .add_columns(Client.full_name)
            .order_by(Payment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[Payment, Optional[str]]]:
        stmt = (
            select(Payment)
            .join(Client, Payment.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(Payment.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def counts_by_status(self) -> dict[str, int]:
        stmt = select(Payment.status, func.count()).group_by(Payment.status)
        rows = (await self.session.execute(stmt)).all()
        return {status: int(count) for status, count in rows}

    async def completed_total_since(self, since: datetime) -> Decimal:
        stmt = (
            select(
                func.coalesce(
                    func.sum(Payment.amount * Payment.exchange_rate), 0
                )
            )
            .select_from(Payment)
            .where(
                Payment.status == PaymentStatus.completed.value,
                Payment.paid_at.is_not(None),
                Payment.paid_at >= since,
            )
        )
        value = (await self.session.execute(stmt)).scalar_one()
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    async def all_payments(self) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.created_at.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def outstanding_total(self) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(PaymentInstallment.amount), 0))
            .select_from(PaymentInstallment)
            .where(PaymentInstallment.status != InstallmentStatus.paid.value)
        )
        value = (await self.session.execute(stmt)).scalar_one()
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))


class PaymentInstallmentRepository(BaseRepository[PaymentInstallment]):
    model = PaymentInstallment

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_payment(
        self, payment_id: UUID
    ) -> list[PaymentInstallment]:
        stmt = (
            select(PaymentInstallment)
            .where(PaymentInstallment.payment_id == payment_id)
            .order_by(PaymentInstallment.due_date.asc().nulls_last())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def paid_sum(self, payment_id: UUID) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(PaymentInstallment.amount), 0))
            .where(
                PaymentInstallment.payment_id == payment_id,
                PaymentInstallment.status == InstallmentStatus.paid.value,
            )
        )
        value = (await self.session.execute(stmt)).scalar_one()
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))


class PaymentOutboxRepository(BaseRepository[PaymentOutbox]):
    model = PaymentOutbox

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def due(
        self, *, limit: int = 50, now: Optional[datetime] = None
    ) -> list[PaymentOutbox]:
        now = now or datetime.now(timezone.utc)
        stmt = (
            select(PaymentOutbox)
            .where(
                PaymentOutbox.status.in_(
                    [OutboxStatus.pending.value, OutboxStatus.failed.value]
                ),
                or_(
                    PaymentOutbox.next_attempt_at.is_(None),
                    PaymentOutbox.next_attempt_at <= now,
                ),
            )
            .order_by(PaymentOutbox.created_at.asc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def for_aggregate(
        self, aggregate_id: UUID
    ) -> list[PaymentOutbox]:
        stmt = (
            select(PaymentOutbox)
            .where(PaymentOutbox.aggregate_id == aggregate_id)
            .order_by(PaymentOutbox.created_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_event_id(
        self, event_id: UUID
    ) -> Optional[PaymentOutbox]:
        stmt = select(PaymentOutbox).where(
            PaymentOutbox.event_id == event_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def search(
        self,
        *,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PaymentOutbox], int]:
        conditions = []
        if status:
            conditions.append(PaymentOutbox.status == status)
        count_stmt = select(func.count()).select_from(PaymentOutbox).where(
            *conditions
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())
        stmt = (
            select(PaymentOutbox)
            .where(*conditions)
            .order_by(PaymentOutbox.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return rows, total
