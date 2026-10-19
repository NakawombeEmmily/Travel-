from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.interaction import InteractionType


class InteractionBase(BaseModel):
    client_id: UUID
    interaction_type: InteractionType = InteractionType.other
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[InteractionType] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None


class InteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    interaction_type: str
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    contacted_by: Optional[UUID] = None
    created_at: datetime


class InteractionListResponse(BaseModel):
    items: list[InteractionRead]
    total: int
    page: int
    page_size: int
