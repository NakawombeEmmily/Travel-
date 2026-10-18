from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    passport_issue_date: Optional[date] = None
    passport_expiry_date: Optional[date] = None
    issuing_country: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact: Optional[str] = None
    consent_given: bool = False
    data_retention_until: Optional[date] = None


class ClientCreate(ClientBase):
    passport_number: str = Field(min_length=4, max_length=64)


class ClientUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    passport_number: Optional[str] = Field(default=None, min_length=4, max_length=64)
    passport_issue_date: Optional[date] = None
    passport_expiry_date: Optional[date] = None
    issuing_country: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact: Optional[str] = None
    consent_given: Optional[bool] = None
    data_retention_until: Optional[date] = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    passport_number_masked: str
    passport_expiring_soon: bool = False
    created_at: datetime
    updated_at: datetime


class ClientReveal(BaseModel):
    passport_number: str


class ClientListResponse(BaseModel):
    items: list[ClientRead]
    total: int
    page: int
    page_size: int
