from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.feedback import Feedback
from app.repositories.feedback import FeedbackRepository
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackRead,
    FeedbackStats,
    FeedbackUpdate,
)
from app.services.exceptions import ClientNotFoundError
from app.services.sentiment import calculate_sentiment


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FeedbackRepository(session)

    def to_read(self, item: Feedback, client_name: Optional[str] = None) -> FeedbackRead:
        read = FeedbackRead.model_validate(item)
        read.client_name = client_name
        return read

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def create(
        self, payload: FeedbackCreate, *, actor_id: Optional[UUID] = None
    ) -> Feedback:
        await self._ensure_client(payload.client_id)
        item = Feedback(
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            rating=payload.rating,
            comment=payload.comment,
            category=payload.category.value if payload.category else None,
            sentiment=calculate_sentiment(payload.rating, payload.comment),
            feedback_date=payload.feedback_date or date.today(),
        )
        await self.repo.add(item)
        return item

    async def update(self, item: Feedback, payload: FeedbackUpdate) -> Feedback:
        data = payload.model_dump(exclude_unset=True)
        if data.get("category") is not None:
            data["category"] = data["category"].value
        for key, value in data.items():
            setattr(item, key, value)
        item.sentiment = calculate_sentiment(item.rating, item.comment)
        await self.session.flush()
        return item

    async def delete(self, item: Feedback) -> None:
        await self.session.delete(item)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FeedbackRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            sentiment=sentiment,
            category=category,
            q=q,
            page=page,
            page_size=page_size,
        )
        return [self.to_read(item, name) for item, name in rows], total

    async def stats(self) -> FeedbackStats:
        count, average = await self.repo.average_rating()
        return FeedbackStats(
            count=count,
            average_rating=round(average, 2),
            by_sentiment=await self.repo.counts_by_sentiment(),
            by_category=await self.repo.counts_by_category(),
        )
