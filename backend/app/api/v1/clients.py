from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_client_ip,
    get_current_user,
    get_encryption_service,
    get_session,
    require_roles,
)
from app.core.security.encryption import EncryptionService
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientRead,
    ClientReveal,
    ClientUpdate,
)
from app.services.audit import record_audit
from app.services.client import ClientService, DuplicatePassportError

router = APIRouter(prefix="/clients", tags=["clients"])


def _service(
    session: AsyncSession, encryption: EncryptionService
) -> ClientService:
    return ClientService(session, encryption)


@router.get("", response_model=ClientListResponse)
async def list_clients(
    q: str | None = None,
    nationality: str | None = None,
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> ClientListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    service = _service(session, encryption)
    items, total = await service.search(
        q=q,
        nationality=nationality,
        page=page,
        page_size=page_size,
        include_deleted=include_deleted and user.role != UserRole.read_only,
    )
    await record_audit(
        session,
        action="read",
        entity_type="client",
        actor_id=user.id,
        metadata={"count": len(items), "q": q},
    )
    await session.commit()
    return ClientListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: "ClientCreate",
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> ClientRead:
    service = _service(session, encryption)
    try:
        client = await service.create(payload, actor_id=user.id)
    except DuplicatePassportError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this passport number already exists",
        )
    await record_audit(
        session,
        action="create",
        entity_type="client",
        actor_id=user.id,
        entity_id=client.id,
    )
    await session.commit()
    return service.to_read(client)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: str,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> ClientRead:
    from uuid import UUID

    client = await session.get(Client, UUID(client_id))
    if client is None or client.is_deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    service = _service(session, encryption)
    await record_audit(
        session,
        action="read",
        entity_type="client",
        actor_id=user.id,
        entity_id=client.id,
    )
    await session.commit()
    return service.to_read(client)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: str,
    payload: "ClientUpdate",
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> ClientRead:
    from uuid import UUID

    client = await session.get(Client, UUID(client_id))
    if client is None or client.is_deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    service = _service(session, encryption)
    try:
        client = await service.update(client, payload, actor_id=user.id)
    except DuplicatePassportError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this passport number already exists",
        )
    await record_audit(
        session,
        action="update",
        entity_type="client",
        actor_id=user.id,
        entity_id=client.id,
    )
    await session.commit()
    return service.to_read(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(get_current_user),
) -> None:
    from uuid import UUID

    client = await session.get(Client, UUID(client_id))
    if client is None or client.is_deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    service = _service(session, encryption)
    await service.soft_delete(client, actor_id=user.id)
    await record_audit(
        session,
        action="delete",
        entity_type="client",
        actor_id=user.id,
        entity_id=client.id,
    )
    await session.commit()


@router.post("/{client_id}/reveal", response_model=ClientReveal)
async def reveal_passport(
    client_id: str,
    session: AsyncSession = Depends(get_session),
    encryption: EncryptionService = Depends(get_encryption_service),
    user: User = Depends(
        require_roles(
            UserRole.super_admin, UserRole.admin, UserRole.agent
        )
    ),
) -> ClientReveal:
    from uuid import UUID

    client = await session.get(Client, UUID(client_id))
    if client is None or client.is_deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    service = _service(session, encryption)
    plaintext = await service.reveal_passport(client)
    await record_audit(
        session,
        action="reveal",
        entity_type="client",
        actor_id=user.id,
        entity_id=client.id,
    )
    await session.commit()
    return ClientReveal(passport_number=plaintext)
