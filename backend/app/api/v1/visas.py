from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.models.visa import Visa
from app.schemas.visa import (
    VisaCreate,
    VisaDetail,
    VisaHistoryRead,
    VisaListResponse,
    VisaRead,
    VisaUpdate,
)
from app.services.audit import record_audit
from app.services.visa import ClientNotFoundError, VisaService

router = APIRouter(prefix="/visas", tags=["visas"])


@router.get("", response_model=VisaListResponse)
async def list_visas(
    client_id: UUID | None = None,
    trip_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    page: int = 1,
    page_size: int = 100,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VisaListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    service = VisaService(session)
    items, total = await service.search(
        client_id=client_id,
        trip_id=trip_id,
        status=status_filter,
        q=q,
        page=page,
        page_size=page_size,
    )
    return VisaListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("", response_model=VisaRead, status_code=status.HTTP_201_CREATED)
async def create_visa(
    payload: VisaCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VisaRead:
    service = VisaService(session)
    try:
        visa = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    await record_audit(
        session,
        action="create",
        entity_type="visa",
        actor_id=user.id,
        entity_id=visa.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(visa.id)
    client_name = row[1] if row else None
    return service.to_read(visa, client_name)


async def _get_visa_or_404(session: AsyncSession, visa_id: UUID) -> Visa:
    visa = await session.get(Visa, visa_id)
    if visa is None:
        raise HTTPException(status_code=404, detail="Visa not found")
    return visa


@router.get("/{visa_id}", response_model=VisaDetail)
async def get_visa(
    visa_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VisaDetail:
    service = VisaService(session)
    row = await service.repo.get_with_client(visa_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Visa not found")
    visa, client_name = row
    return await service.detail(visa, client_name)


@router.get("/{visa_id}/history", response_model=list[VisaHistoryRead])
async def get_visa_history(
    visa_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[VisaHistoryRead]:
    await _get_visa_or_404(session, visa_id)
    service = VisaService(session)
    history = await service.repo.history(visa_id)
    return [VisaHistoryRead.model_validate(h) for h in history]


@router.patch("/{visa_id}", response_model=VisaRead)
async def update_visa(
    visa_id: UUID,
    payload: VisaUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VisaRead:
    visa = await _get_visa_or_404(session, visa_id)
    service = VisaService(session)
    visa = await service.update(visa, payload, actor_id=user.id)
    await record_audit(
        session,
        action="update",
        entity_type="visa",
        actor_id=user.id,
        entity_id=visa.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(visa.id)
    client_name = row[1] if row else None
    return service.to_read(visa, client_name)


@router.delete("/{visa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visa(
    visa_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    visa = await _get_visa_or_404(session, visa_id)
    service = VisaService(session)
    await service.delete(visa)
    await record_audit(
        session,
        action="delete",
        entity_type="visa",
        actor_id=user.id,
        entity_id=visa_id,
    )
    await session.commit()
