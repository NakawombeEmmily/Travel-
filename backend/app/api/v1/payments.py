from __future__ import annotations

import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session, require_roles
from app.models.payment import Payment, PaymentInstallment
from app.models.user import User, UserRole
from app.repositories.admin import AdminRevenueSummaryRepository
from app.repositories.payment import PaymentOutboxRepository
from app.schemas.payment import (
    OutboxEventRead,
    OutboxListResponse,
    OutboxProcessResult,
    PaymentCreate,
    PaymentListResponse,
    PaymentRead,
    PaymentStats,
    PaymentUpdate,
    ReconcileResult,
    RevenueSummaryRead,
)
from app.services.audit import record_audit
from app.services.exceptions import (
    ClientNotFoundError,
    ConflictError,
    NotFoundError,
    PaymentError,
)
from app.services.outbox import OutboxService
from app.services.payment import PaymentService
from app.services.payment_providers import PaymentProviderError
from app.services.reconciliation import ReconciliationService

router = APIRouter(prefix="/payments", tags=["payments"])

ACCOUNTING_ROLES = (
    UserRole.super_admin,
    UserRole.admin,
    UserRole.accountant,
)


async def _get_or_404(session: AsyncSession, payment_id: UUID) -> Payment:
    payment = await session.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


async def _flush_outbox(session: AsyncSession, payment_id: UUID) -> None:
    try:
        await OutboxService(session).process_for_payment(payment_id)
    except Exception:  # noqa: BLE001 - retries handled by the worker
        pass
    await session.commit()


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    client_id: UUID | None = None,
    trip_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    provider: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items, total = await PaymentService(session).list(
        client_id=client_id,
        trip_id=trip_id,
        status=status_filter,
        provider=provider,
        q=q,
        page=page,
        page_size=page_size,
    )
    return PaymentListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/stats", response_model=PaymentStats)
async def payment_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentStats:
    return await PaymentService(session).stats()


@router.get("/revenue", response_model=list[RevenueSummaryRead])
async def revenue_summaries(
    limit: int = 30,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[RevenueSummaryRead]:
    rows = await AdminRevenueSummaryRepository(session).list_recent(
        limit=min(max(limit, 1), 200)
    )
    return [RevenueSummaryRead.model_validate(row) for row in rows]


@router.get("/outbox", response_model=OutboxListResponse)
async def list_outbox(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(*ACCOUNTING_ROLES)),
) -> OutboxListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    rows, total = await PaymentOutboxRepository(session).search(
        status=status_filter, page=page, page_size=page_size
    )
    return OutboxListResponse(
        items=[OutboxEventRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/outbox/process", response_model=OutboxProcessResult)
async def process_outbox(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(*ACCOUNTING_ROLES)),
) -> OutboxProcessResult:
    result = await OutboxService(session).process_pending(
        limit=min(max(limit, 1), 200)
    )
    await record_audit(
        session,
        action="process",
        entity_type="payment_outbox",
        actor_id=user.id,
        metadata=result,
    )
    await session.commit()
    return OutboxProcessResult(**result)


@router.post("/outbox/{event_id}/retry", response_model=OutboxEventRead)
async def retry_outbox(
    event_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(*ACCOUNTING_ROLES)),
) -> OutboxEventRead:
    event = await OutboxService(session).retry(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Outbox event not found")
    await record_audit(
        session,
        action="retry",
        entity_type="payment_outbox",
        actor_id=user.id,
        entity_id=event.id,
    )
    await session.commit()
    return OutboxEventRead.model_validate(event)


@router.post("/reconcile", response_model=ReconcileResult)
async def reconcile_payments(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(*ACCOUNTING_ROLES)),
) -> ReconcileResult:
    result = await ReconciliationService(session).reconcile()
    await record_audit(
        session,
        action="reconcile",
        entity_type="payment",
        actor_id=user.id,
        metadata=result.model_dump(),
    )
    await session.commit()
    return result


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentRead:
    service = PaymentService(session)
    try:
        payment = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError:
        raise HTTPException(status_code=404, detail="Client not found")
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (PaymentError, PaymentProviderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await record_audit(
        session,
        action="create",
        entity_type="payment",
        actor_id=user.id,
        entity_id=payment.id,
        metadata={"amount": str(payment.amount), "currency": payment.currency},
    )
    await session.commit()
    await _flush_outbox(session, payment.id)
    return await service.get_read(payment.id)


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentRead:
    try:
        return await PaymentService(session).get_read(payment_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.patch("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: UUID,
    payload: PaymentUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentRead:
    payment = await _get_or_404(session, payment_id)
    service = PaymentService(session)
    payment = await service.update(payment, payload)
    await record_audit(
        session,
        action="update",
        entity_type="payment",
        actor_id=user.id,
        entity_id=payment.id,
    )
    await session.commit()
    await _flush_outbox(session, payment.id)
    return await service.get_read(payment.id)


@router.post("/{payment_id}/refund", response_model=PaymentRead)
async def refund_payment(
    payment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(*ACCOUNTING_ROLES)),
) -> PaymentRead:
    payment = await _get_or_404(session, payment_id)
    service = PaymentService(session)
    try:
        payment = await service.refund(payment)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await record_audit(
        session,
        action="refund",
        entity_type="payment",
        actor_id=user.id,
        entity_id=payment.id,
    )
    await session.commit()
    await _flush_outbox(session, payment.id)
    return await service.get_read(payment.id)


@router.post(
    "/{payment_id}/installments/{installment_id}/pay",
    response_model=PaymentRead,
)
async def pay_installment(
    payment_id: UUID,
    installment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PaymentRead:
    payment = await _get_or_404(session, payment_id)
    installment = await session.get(PaymentInstallment, installment_id)
    if installment is None or installment.payment_id != payment.id:
        raise HTTPException(status_code=404, detail="Installment not found")
    service = PaymentService(session)
    record = payment
    try:
        record = await service.pay_installment(payment, installment)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await record_audit(
        session,
        action="installment_payment",
        entity_type="payment",
        actor_id=user.id,
        entity_id=record.id,
        metadata={"installment_id": str(installment_id)},
    )
    await session.commit()
    await _flush_outbox(session, record.id)
    return await service.get_read(record.id)


@router.get("/{payment_id}/invoice")
async def download_invoice(
    payment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    service = PaymentService(session)
    try:
        payment, _ = await service.get(payment_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")

    ledger = await service.ledger.ledger_repo.get_by_payment(payment.id)
    if ledger is None:
        ledger = await service.ledger.sync_payment(payment)
    invoice = await service.ledger.invoice_repo.get_by_ledger(ledger.id)
    if invoice is None:
        if not payment.invoice_number:
            raise HTTPException(
                status_code=404, detail="Invoice is not available yet"
            )
        invoice = await service.ledger.ensure_invoice(ledger, payment)
    try:
        data = service.storage.read(invoice.pdf_key)
    except FileNotFoundError:
        await service.ledger.write_invoice_pdf(invoice, payment)
        data = service.storage.read(invoice.pdf_key)
    await record_audit(
        session,
        action="download",
        entity_type="payment_invoice",
        actor_id=user.id,
        entity_id=payment.id,
        metadata={"invoice_number": invoice.invoice_number},
    )
    await session.commit()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{invoice.invoice_number}.pdf"'
            )
        },
    )
