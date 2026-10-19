from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.visa import VisaStatus


class VisaBase(BaseModel):
    client_id: UUID
    trip_id: Optional[UUID] = None
    destination_country: str = Field(min_length=1, max_length=100)
    visa_type: Optional[str] = None
    application_date: Optional[date] = None
    submission_date: Optional[date] = None
    reference_number: Optional[str] = None
    status: VisaStatus = VisaStatus.not_started
    approval_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None


class VisaCreate(VisaBase):
    pass


class VisaUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    destination_country: Optional[str] = Field(default=None, min_length=1, max_length=100)
    visa_type: Optional[str] = None
    application_date: Optional[date] = None
    submission_date: Optional[date] = None
    reference_number: Optional[str] = None
    status: Optional[VisaStatus] = None
    approval_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    status_note: Optional[str] = None


class VisaHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[UUID] = None
    changed_at: datetime
    note: Optional[str] = None


class VisaRead(VisaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VisaDetail(VisaRead):
    history: list[VisaHistoryRead] = []


class VisaListResponse(BaseModel):
    items: list[VisaRead]
    total: int
    page: int
    page_size: int
