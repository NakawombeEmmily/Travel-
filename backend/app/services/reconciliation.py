from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payment import PaymentRepository
from app.schemas.payment import ReconcileResult
from app.services.ledger import LedgerService
from app.services.storage import LocalStorage


class ReconciliationService:
    """Compares crm payments with the admin ledger and repairs drift."""

    def __init__(
        self, session: AsyncSession, storage: Optional[LocalStorage] = None
    ) -> None:
        self.session = session
        self.ledger = LedgerService(session, storage)
        self.payments = PaymentRepository(session)

    async def reconcile(self) -> ReconcileResult:
        ledger_repo = self.ledger.ledger_repo
        payments = await self.payments.all_payments()
        created = updated = mismatched = 0
        errors: list[str] = []
        currencies: set[str] = set()

        for payment in payments:
            currencies.add(payment.currency)
            try:
                existing = await ledger_repo.get_by_payment(payment.id)
                if existing is None:
                    ledger = await self.ledger.sync_payment(payment)
                    ledger.last_reconciled_at = datetime.now(timezone.utc)
                    created += 1
                    continue

                expected_amount = await self.ledger.paid_amount(payment)
                drifted = (
                    existing.status != payment.status
                    or Decimal(existing.amount) != expected_amount
                    or existing.invoice_number != payment.invoice_number
                )
                if drifted:
                    updated += 1
                    mismatched += 1
                    ledger = await self.ledger.sync_payment(payment)
                    ledger.last_reconciled_at = datetime.now(timezone.utc)
                else:
                    existing.last_reconciled_at = datetime.now(timezone.utc)
            except Exception as exc:  # noqa: BLE001 - collect and continue
                errors.append(f"{payment.id}: {exc}")

        for currency in currencies:
            await self.ledger.refresh_revenue_summary(currency)
        await self.session.flush()
        return ReconcileResult(
            checked=len(payments),
            created=created,
            updated=updated,
            mismatched=mismatched,
            errors=errors,
        )
