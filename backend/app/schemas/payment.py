from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod


class InstallmentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    due_date: Optional[date] = None


class InstallmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: UUID
    amount: Decimal
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    status: str
    created_at: datetime


class PaymentCreate(BaseModel):
    client_id: UUID
    trip_id: Optional[UUID] = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1.0"), gt=0)
    method: PaymentMethod = PaymentMethod.cash
    provider: Optional[str] = None
    notes: Optional[str] = None
    installments: list[InstallmentCreate] = []


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    method: Optional[PaymentMethod] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    trip_id: Optional[UUID] = None
    amount: Decimal
    currency: str
    exchange_rate: Decimal
    method: str
    provider: str
    provider_transaction_id: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    installments: list[InstallmentRead] = []


class PaymentListResponse(BaseModel):
    items: list[PaymentRead]
    total: int
    page: int
    page_size: int


class PaymentStats(BaseModel):
    count: int
    by_status: dict[str, int]
    total_collected: Decimal
    outstanding: Decimal


class OutboxEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    status: str
    attempts: int
    max_attempts: int
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class OutboxListResponse(BaseModel):
    items: list[OutboxEventRead]
    total: int
    page: int
    page_size: int


class OutboxProcessResult(BaseModel):
    processed: int
    completed: int
    failed: int
    pending: int


class ReconcileResult(BaseModel):
    checked: int
    created: int
    updated: int
    mismatched: int
    errors: list[str] = []


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ledger_id: UUID
    invoice_number: str
    issue_date: date
    due_date: Optional[date] = None
    amount: Decimal
    status: str
    pdf_key: Optional[str] = None
    created_at: datetime


class RevenueSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    summary_date: date
    period_type: str
    total_amount: Decimal
    currency: str
    transaction_count: int
    completed_count: int
    failed_count: int
    refunded_count: int
    created_at: datetime
