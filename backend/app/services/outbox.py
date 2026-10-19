from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.payment import EventTypes, OutboxStatus, Payment, PaymentOutbox
from app.repositories.payment import PaymentOutboxRepository, PaymentRepository
from app.services.ledger import LedgerService


class OutboxService:
    """Transactional outbox publisher for payment domain events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PaymentOutboxRepository(session)
        self.payments = PaymentRepository(session)
        self.ledger = LedgerService(session)

    async def enqueue(
        self,
        payment: Payment,
        event_type: str,
    ) -> PaymentOutbox:
        event = PaymentOutbox(
            event_id=uuid4(),
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type=event_type,
            payload={
                "payment_id": str(payment.id),
                "client_id": str(payment.client_id),
                "trip_id": str(payment.trip_id) if payment.trip_id else None,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "invoice_number": payment.invoice_number,
            },
            status=OutboxStatus.pending.value,
            max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
        )
        await self.repo.add(event)
        return event

    async def _handle(self, event: PaymentOutbox) -> None:
        payment = await self.session.get(Payment, event.aggregate_id)
        if payment is None:
            raise ValueError(f"Payment {event.aggregate_id} not found")
        await self.ledger.sync_payment(payment)
        await self.ledger.refresh_revenue_summary(payment.currency)

    async def process(self, event: PaymentOutbox) -> bool:
        """Process a single event. Returns True when it completed."""
        now = datetime.now(timezone.utc)
        event.attempts = (event.attempts or 0) + 1
        event.last_attempt_at = now
        event.status = OutboxStatus.processing.value
        try:
            await self._handle(event)
        except Exception as exc:  # noqa: BLE001 - captured for retry/dead-letter
            event.error_message = str(exc)[:1000]
            if event.attempts >= event.max_attempts:
                event.status = OutboxStatus.dead_letter.value
            else:
                event.status = OutboxStatus.failed.value
                backoff = min(2 ** event.attempts, 300)
                event.next_attempt_at = now + timedelta(seconds=backoff)
            await self.session.flush()
            return False
        event.status = OutboxStatus.completed.value
        event.processed_at = now
        event.error_message = None
        await self.session.flush()
        return True

    async def process_pending(self, *, limit: int = 50) -> dict[str, int]:
        events = await self.repo.due(limit=limit)
        completed = failed = 0
        for event in events:
            ok = await self.process(event)
            if ok:
                completed += 1
            else:
                failed += 1
        if completed or failed:
            await self.session.commit()
        pending = sum(
            1
            for event in await self.repo.due(limit=1000)
        )
        return {
            "processed": len(events),
            "completed": completed,
            "failed": failed,
            "pending": pending,
        }

    async def process_for_payment(self, payment_id: UUID) -> int:
        """Best-effort synchronous flush of pending events for one payment."""
        events = await self.repo.for_aggregate(payment_id)
        processed = 0
        for event in events:
            if event.status in (
                OutboxStatus.pending.value,
                OutboxStatus.failed.value,
            ):
                await self.process(event)
                processed += 1
        return processed

    async def retry(self, event_id: UUID) -> Optional[PaymentOutbox]:
        event = await self.repo.get_by_event_id(event_id)
        if event is None:
            return None
        event.status = OutboxStatus.pending.value
        event.attempts = 0
        event.next_attempt_at = None
        event.error_message = None
        await self.session.flush()
        return event
