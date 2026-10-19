from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.trip import TripPurpose, TripStatus


class TripBase(BaseModel):
    client_id: UUID
    destination_country: str = Field(min_length=1, max_length=100)
    travel_start_date: date
    travel_end_date: Optional[date] = None
    purpose: TripPurpose = TripPurpose.tourism
    itinerary_notes: Optional[str] = None
    total_cost: Decimal = Decimal("0.00")
    currency: str = Field(default="USD", max_length=3)
    status: TripStatus = TripStatus.inquiry


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    destination_country: Optional[str] = Field(default=None, min_length=1, max_length=100)
    travel_start_date: Optional[date] = None
    travel_end_date: Optional[date] = None
    purpose: Optional[TripPurpose] = None
    itinerary_notes: Optional[str] = None
    total_cost: Optional[Decimal] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    status: Optional[TripStatus] = None


class TripRead(TripBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TripListResponse(BaseModel):
    items: list[TripRead]
    total: int
    page: int
    page_size: int
