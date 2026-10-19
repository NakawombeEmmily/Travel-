from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.feedback import FeedbackCategory, Sentiment


class FeedbackBase(BaseModel):
    client_id: UUID
    trip_id: Optional[UUID] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    category: Optional[FeedbackCategory] = None
    feedback_date: Optional[date] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    category: Optional[FeedbackCategory] = None
    feedback_date: Optional[date] = None


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    trip_id: Optional[UUID] = None
    rating: int
    comment: Optional[str] = None
    category: Optional[str] = None
    sentiment: str
    feedback_date: date
    created_at: datetime


class FeedbackListResponse(BaseModel):
    items: list[FeedbackRead]
    total: int
    page: int
    page_size: int


class FeedbackStats(BaseModel):
    count: int
    average_rating: float
    by_sentiment: dict[str, int]
    by_category: dict[str, int]
