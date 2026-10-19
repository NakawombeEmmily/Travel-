from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin import AdminInvoice, AdminLedger, AdminRevenueSummary
from app.models.client import Client
from app.models.payment import Payment, PaymentStatus
from app.repositories.admin import (
    AdminInvoiceRepository,
    AdminLedgerRepository,
    AdminRevenueSummaryRepository,
)
from app.repositories.payment import PaymentInstallmentRepository
from app.services.pdf import build_invoice_pdf
from app.services.storage import LocalStorage, get_storage


class LedgerService:
    """Keeps the admin schema in sync with crm payments."""

    def __init__(
        self, session: AsyncSession, storage: Optional[LocalStorage] = None
    ) -> None:
        self.session = session
        self.storage = storage or get_storage()
        self.ledger_repo = AdminLedgerRepository(session)
        self.invoice_repo = AdminInvoiceRepository(session)
        self.revenue_repo = AdminRevenueSummaryRepository(session)
        self.installment_repo = PaymentInstallmentRepository(session)

    async def paid_amount(self, payment: Payment) -> Decimal:
        if payment.status == PaymentStatus.refunded.value:
            return Decimal("0.00")
        if payment.status == PaymentStatus.partial.value:
            return await self.installment_repo.paid_sum(payment.id)
        return Decimal(payment.amount)

    async def sync_payment(self, payment: Payment) -> AdminLedger:
        ledger = await self.ledger_repo.get_by_payment(payment.id)
        amount = await self.paid_amount(payment)
        if ledger is None:
            ledger = AdminLedger(
                crm_payment_id=payment.id,
                client_id=payment.client_id,
                trip_id=payment.trip_id,
                amount=amount,
                currency=payment.currency,
                status=payment.status,
                provider=payment.provider,
                provider_transaction_id=payment.provider_transaction_id,
                invoice_number=payment.invoice_number,
            )
            await self.ledger_repo.add(ledger)
        else:
            ledger.client_id = payment.client_id
            ledger.trip_id = payment.trip_id
            ledger.amount = amount
            ledger.currency = payment.currency
            ledger.status = payment.status
            ledger.provider = payment.provider
            ledger.provider_transaction_id = payment.provider_transaction_id
            ledger.invoice_number = payment.invoice_number
            ledger.synced_at = datetime.now(timezone.utc)
            await self.session.flush()

        if (
            payment.status in (PaymentStatus.completed.value, PaymentStatus.partial.value)
            and payment.invoice_number
        ):
            await self.ensure_invoice(ledger, payment)
        return ledger

    async def ensure_invoice(
        self, ledger: AdminLedger, payment: Payment
    ) -> AdminInvoice:
        existing = await self.invoice_repo.get_by_ledger(ledger.id)
        if existing is None and payment.invoice_number:
            existing = await self.invoice_repo.get_by_number(
                payment.invoice_number
            )
        if existing is not None:
            return existing

        paid_on = payment.paid_at or datetime.now(timezone.utc)
        issue_date = paid_on.date()
        due_date = issue_date + timedelta(days=settings.INVOICE_DUE_DAYS)

        invoice = AdminInvoice(
            ledger_id=ledger.id,
            invoice_number=payment.invoice_number or "INV-DRAFT",
            issue_date=issue_date,
            due_date=due_date,
            amount=ledger.amount,
            status=payment.status,
            pdf_key=f"invoices/{payment.invoice_number or ledger.id}.pdf",
        )
        await self.invoice_repo.add(invoice)
        await self.write_invoice_pdf(invoice, payment)
        return invoice

    async def write_invoice_pdf(
        self, invoice: AdminInvoice, payment: Payment
    ) -> None:
        client = await self.session.get(Client, payment.client_id)
        pdf_bytes = build_invoice_pdf(
            invoice_number=invoice.invoice_number,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            client_name=client.full_name if client else "Client",
            client_email=client.email if client else None,
            currency=payment.currency,
            amount=invoice.amount,
            status=payment.status,
            notes=payment.notes,
        )
        key = invoice.pdf_key or f"invoices/{invoice.invoice_number}.pdf"
        self.storage.save(key, pdf_bytes)
        invoice.pdf_key = key
        await self.session.flush()

    async def refresh_revenue_summary(
        self, currency: str, day: Optional[date] = None
    ) -> list[AdminRevenueSummary]:
        day = day or date.today()
        month_start = day.replace(day=1)
        last_day = calendar.monthrange(day.year, day.month)[1]
        month_end = day.replace(day=last_day)

        summaries: list[AdminRevenueSummary] = []
        for period_type, start, end in (
            ("daily", day, day),
            ("monthly", month_start, month_end),
        ):
            totals = await self.ledger_repo.totals_range(start, end, currency)
            summary = await self.revenue_repo.get_entry(
                month_start if period_type == "monthly" else day,
                period_type,
                currency,
            )
            summary_date = month_start if period_type == "monthly" else day
            if summary is None:
                summary = AdminRevenueSummary(
                    summary_date=summary_date,
                    period_type=period_type,
                    total_amount=Decimal(totals["total_amount"]),
                    currency=currency,
                    transaction_count=int(totals["transaction_count"]),
                    completed_count=int(totals["completed_count"]),
                    failed_count=int(totals["failed_count"]),
                    refunded_count=int(totals["refunded_count"]),
                )
                await self.revenue_repo.add(summary)
            else:
                summary.total_amount = Decimal(totals["total_amount"])
                summary.transaction_count = int(totals["transaction_count"])
                summary.completed_count = int(totals["completed_count"])
                summary.failed_count = int(totals["failed_count"])
                summary.refunded_count = int(totals["refunded_count"])
                await self.session.flush()
            summaries.append(summary)
        return summaries
