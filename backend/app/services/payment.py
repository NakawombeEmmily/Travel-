from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.payment import (
    EventTypes,
    InstallmentStatus,
    Payment,
    PaymentInstallment,
    PaymentStatus,
)
from app.models.trip import Trip
from app.repositories.payment import (
    PaymentInstallmentRepository,
    PaymentRepository,
)
from app.schemas.payment import (
    InstallmentRead,
    PaymentCreate,
    PaymentRead,
    PaymentStats,
    PaymentUpdate,
)
from app.services.exceptions import (
    ClientNotFoundError,
    ConflictError,
    NotFoundError,
    PaymentError,
)
from app.services.ledger import LedgerService
from app.services.outbox import OutboxService
from app.services.payment_providers import (
    PaymentProvider,
    get_payment_provider,
)
from app.services.storage import LocalStorage, get_storage


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        provider: Optional[PaymentProvider] = None,
        storage: Optional[LocalStorage] = None,
    ) -> None:
        self.session = session
        self.provider = provider or get_payment_provider()
        self.storage = storage or get_storage()
        self.repo = PaymentRepository(session)
        self.installments = PaymentInstallmentRepository(session)
        self.outbox = OutboxService(session)
        self.ledger = LedgerService(session, self.storage)

    def to_read(
        self,
        payment: Payment,
        *,
        client_name: Optional[str] = None,
        installments: Optional[list[PaymentInstallment]] = None,
    ) -> PaymentRead:
        read = PaymentRead.model_validate(payment)
        read.client_name = client_name
        read.installments = [
            InstallmentRead.model_validate(item) for item in (installments or [])
        ]
        return read

    async def _ensure_client(self, client_id: UUID) -> Client:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))
        return client

    async def _ensure_trip(self, trip_id: UUID) -> None:
        trip = await self.session.get(Trip, trip_id)
        if trip is None:
            raise NotFoundError("Trip not found")

    def _generate_invoice_number(self) -> str:
        now = datetime.now(timezone.utc)
        return f"INV-{now:%Y%m}-{uuid4().hex[:6].upper()}"

    async def create(
        self, payload: PaymentCreate, *, actor_id: Optional[UUID] = None
    ) -> Payment:
        await self._ensure_client(payload.client_id)
        if payload.trip_id is not None:
            await self._ensure_trip(payload.trip_id)

        provider_name = (payload.provider or self.provider.name).lower()
        provider = get_payment_provider(provider_name)
        currency = payload.currency.upper()
        method = payload.method.value

        installments = list(payload.installments)
        if installments:
            total = sum((item.amount for item in installments), Decimal("0.00"))
            if total != Decimal(payload.amount):
                raise PaymentError(
                    "Installment amounts must sum to the payment amount"
                )
            status = PaymentStatus.partial.value
            paid_at = None
            tx_id = None
            invoice_number = None
        else:
            result = provider.charge(
                amount=Decimal(payload.amount),
                currency=currency,
                method=method,
                reference=str(payload.client_id),
            )
            if not result.success:
                raise PaymentError(result.message or "Payment was declined")
            status = PaymentStatus.completed.value
            paid_at = datetime.now(timezone.utc)
            tx_id = result.provider_transaction_id
            invoice_number = self._generate_invoice_number()

        payment = Payment(
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            amount=Decimal(payload.amount),
            currency=currency,
            exchange_rate=Decimal(payload.exchange_rate),
            method=method,
            provider=provider_name,
            provider_transaction_id=tx_id,
            status=status,
            paid_at=paid_at,
            invoice_number=invoice_number,
            notes=payload.notes,
            created_by=actor_id,
        )
        await self.repo.add(payment)

        for item in installments:
            self.session.add(
                PaymentInstallment(
                    payment_id=payment.id,
                    amount=Decimal(item.amount),
                    due_date=item.due_date,
                    status=InstallmentStatus.pending.value,
                )
            )
        await self.session.flush()

        await self.outbox.enqueue(payment, EventTypes.payment_created)
        return payment

    async def pay_installment(
        self, payment: Payment, installment: PaymentInstallment
    ) -> Payment:
        if installment.status == InstallmentStatus.paid.value:
            raise ConflictError("Installment already paid")
        if payment.status == PaymentStatus.refunded.value:
            raise PaymentError("Payment has been refunded")
        provider = get_payment_provider(payment.provider)
        result = provider.charge(
            amount=Decimal(installment.amount),
            currency=payment.currency,
            method=payment.method,
            reference=str(installment.id),
        )
        if not result.success:
            raise PaymentError(result.message or "Installment payment declined")

        installment.status = InstallmentStatus.paid.value
        installment.paid_at = datetime.now(timezone.utc)

        all_items = await self.installments.list_for_payment(payment.id)
        all_paid = all(
            item.status == InstallmentStatus.paid.value for item in all_items
        )
        if all_paid:
            payment.status = PaymentStatus.completed.value
            payment.paid_at = datetime.now(timezone.utc)
            payment.provider_transaction_id = result.provider_transaction_id
            if not payment.invoice_number:
                payment.invoice_number = self._generate_invoice_number()
        else:
            payment.status = PaymentStatus.partial.value
        await self.session.flush()

        await self.outbox.enqueue(payment, EventTypes.payment_updated)
        return payment

    async def refund(self, payment: Payment) -> Payment:
        if payment.status != PaymentStatus.completed.value:
            raise PaymentError("Only completed payments can be refunded")
        if not payment.provider_transaction_id:
            raise PaymentError("No provider transaction to refund")
        provider = get_payment_provider(payment.provider)
        result = provider.refund(
            provider_transaction_id=payment.provider_transaction_id,
            amount=Decimal(payment.amount),
            currency=payment.currency,
        )
        if not result.success:
            raise PaymentError(result.message or "Refund was declined")
        payment.status = PaymentStatus.refunded.value
        await self.session.flush()
        await self.outbox.enqueue(payment, EventTypes.payment_refunded)
        return payment

    async def update(
        self, payment: Payment, payload: PaymentUpdate
    ) -> Payment:
        data = payload.model_dump(exclude_unset=True)
        if data.get("method") is not None:
            data["method"] = data["method"].value
        for key, value in data.items():
            setattr(payment, key, value)
        if (
            payment.status == PaymentStatus.completed.value
            and payment.paid_at is None
        ):
            payment.paid_at = datetime.now(timezone.utc)
        if (
            payment.status == PaymentStatus.completed.value
            and not payment.invoice_number
        ):
            payment.invoice_number = self._generate_invoice_number()
        await self.session.flush()
        await self.outbox.enqueue(payment, EventTypes.payment_updated)
        return payment

    async def list(
        self,
        *,
        client_id: Optional[UUID] = None,
        trip_id: Optional[UUID] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PaymentRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            trip_id=trip_id,
            status=status,
            provider=provider,
            q=q,
            page=page,
            page_size=page_size,
        )
        items: list[PaymentRead] = []
        for payment, client_name in rows:
            installments = await self.installments.list_for_payment(payment.id)
            items.append(
                self.to_read(
                    payment,
                    client_name=client_name,
                    installments=installments,
                )
            )
        return items, total

    async def get(self, payment_id: UUID) -> tuple[Payment, Optional[str]]:
        row = await self.repo.get_with_client(payment_id)
        if row is None:
            raise NotFoundError("Payment not found")
        return row

    async def get_read(
        self, payment_id: UUID
    ) -> PaymentRead:
        payment, client_name = await self.get(payment_id)
        installments = await self.installments.list_for_payment(payment.id)
        return self.to_read(
            payment, client_name=client_name, installments=installments
        )

    async def stats(self) -> PaymentStats:
        by_status = await self.repo.counts_by_status()
        total_collected = await self.repo.completed_total_since(
            datetime(1970, 1, 1, tzinfo=timezone.utc)
        )
        outstanding = await self.repo.outstanding_total()
        return PaymentStats(
            count=sum(by_status.values()),
            by_status=by_status,
            total_collected=total_collected,
            outstanding=outstanding,
        )
