from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackRead,
    FeedbackStats,
    FeedbackUpdate,
)
from app.services.audit import record_audit
from app.services.exceptions import ClientNotFoundError
from app.services.feedback import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    client_id: UUID | None = None,
    sentiment: str | None = None,
    category: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FeedbackListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    items, total = await FeedbackService(session).search(
        client_id=client_id,
        sentiment=sentiment,
        category=category,
        q=q,
        page=page,
        page_size=page_size,
    )
    return FeedbackListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/stats", response_model=FeedbackStats)
async def feedback_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FeedbackStats:
    return await FeedbackService(session).stats()


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    payload: FeedbackCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FeedbackRead:
    service = FeedbackService(session)
    try:
        item = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError:
        raise HTTPException(status_code=404, detail="Client not found")
    await record_audit(
        session,
        action="create",
        entity_type="feedback",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


async def _get_or_404(session: AsyncSession, feedback_id: UUID) -> Feedback:
    item = await session.get(Feedback, feedback_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return item


@router.get("/{feedback_id}", response_model=FeedbackRead)
async def get_feedback(
    feedback_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FeedbackRead:
    service = FeedbackService(session)
    row = await service.repo.get_with_client(feedback_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    item, name = row
    return service.to_read(item, name)


@router.patch("/{feedback_id}", response_model=FeedbackRead)
async def update_feedback(
    feedback_id: UUID,
    payload: FeedbackUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FeedbackRead:
    item = await _get_or_404(session, feedback_id)
    service = FeedbackService(session)
    item = await service.update(item, payload)
    await record_audit(
        session,
        action="update",
        entity_type="feedback",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    item = await _get_or_404(session, feedback_id)
    await FeedbackService(session).delete(item)
    await record_audit(
        session,
        action="delete",
        entity_type="feedback",
        actor_id=user.id,
        entity_id=feedback_id,
    )
    await session.commit()
