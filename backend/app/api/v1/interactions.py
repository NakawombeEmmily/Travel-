from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session, require_write_access
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.interaction import (
    InteractionCreate,
    InteractionListResponse,
    InteractionRead,
    InteractionUpdate,
)
from app.services.audit import record_audit
from app.services.exceptions import ClientNotFoundError
from app.services.interaction import InteractionService

router = APIRouter(
    prefix="/interactions",
    tags=["interactions"],
    dependencies=[Depends(require_write_access)],
)


@router.get("", response_model=InteractionListResponse)
async def list_interactions(
    client_id: UUID | None = None,
    interaction_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> InteractionListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    items, total = await InteractionService(session).search(
        client_id=client_id,
        interaction_type=interaction_type,
        page=page,
        page_size=page_size,
    )
    return InteractionListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post(
    "", response_model=InteractionRead, status_code=status.HTTP_201_CREATED
)
async def create_interaction(
    payload: InteractionCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> InteractionRead:
    service = InteractionService(session)
    try:
        item = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    await record_audit(
        session,
        action="create",
        entity_type="interaction",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


async def _get_or_404(session: AsyncSession, interaction_id: UUID) -> Interaction:
    item = await session.get(Interaction, interaction_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return item


@router.get("/{interaction_id}", response_model=InteractionRead)
async def get_interaction(
    interaction_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> InteractionRead:
    service = InteractionService(session)
    row = await service.repo.get_with_client(interaction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    item, name = row
    return service.to_read(item, name)


@router.patch("/{interaction_id}", response_model=InteractionRead)
async def update_interaction(
    interaction_id: UUID,
    payload: InteractionUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> InteractionRead:
    item = await _get_or_404(session, interaction_id)
    service = InteractionService(session)
    item = await service.update(item, payload)
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    interaction_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    item = await _get_or_404(session, interaction_id)
    await InteractionService(session).delete(item)
    await record_audit(
        session,
        action="delete",
        entity_type="interaction",
        actor_id=user.id,
        entity_id=interaction_id,
    )
    await session.commit()
