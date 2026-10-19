from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import LeadStatus


class LeadBase(BaseModel):
    client_id: Optional[UUID] = None
    full_name: str = Field(min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=50)
    status: LeadStatus = LeadStatus.lead
    assigned_to: Optional[UUID] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    client_id: Optional[UUID] = None
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=50)
    status: Optional[LeadStatus] = None
    assigned_to: Optional[UUID] = None


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: Optional[UUID] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: str
    assigned_to: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    items: list[LeadRead]
    total: int
    page: int
    page_size: int
