from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VisaStatus(str, Enum):
    not_required = "not_required"
    not_started = "not_started"
    documents_pending = "documents_pending"
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class Visa(Base):
    __tablename__ = "visas"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    destination_country: Mapped[str] = mapped_column(String(100), nullable=False)
    visa_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    application_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    submission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default=VisaStatus.not_started.value
    )
    approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class VisaStatusHistory(Base):
    __tablename__ = "visa_status_history"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
