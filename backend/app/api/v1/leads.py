from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadListResponse, LeadRead, LeadUpdate
from app.services.audit import record_audit
from app.services.lead import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> LeadListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items, total = await LeadService(session).search(
        status=status_filter, q=q, page=page, page_size=page_size
    )
    return LeadListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> LeadRead:
    service = LeadService(session)
    item = await service.create(payload, actor_id=user.id)
    await record_audit(
        session,
        action="create",
        entity_type="lead",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    return service.to_read(item)


async def _get_or_404(session: AsyncSession, lead_id: UUID) -> Lead:
    item = await session.get(Lead, lead_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return item


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> LeadRead:
    return LeadService(session).to_read(await _get_or_404(session, lead_id))


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> LeadRead:
    item = await _get_or_404(session, lead_id)
    service = LeadService(session)
    item = await service.update(item, payload)
    await record_audit(
        session,
        action="update",
        entity_type="lead",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    return service.to_read(item)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    item = await _get_or_404(session, lead_id)
    await LeadService(session).delete(item)
    await record_audit(
        session,
        action="delete",
        entity_type="lead",
        actor_id=user.id,
        entity_id=lead_id,
    )
    await session.commit()
