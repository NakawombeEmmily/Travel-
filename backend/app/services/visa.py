from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.visa import Visa, VisaStatus, VisaStatusHistory
from app.repositories.visa import VisaRepository
from app.schemas.visa import (
    VisaCreate,
    VisaDetail,
    VisaHistoryRead,
    VisaRead,
    VisaUpdate,
)


class ClientNotFoundError(Exception):
    pass


class VisaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VisaRepository(session)

    def to_read(self, visa: Visa, client_name: Optional[str] = None) -> VisaRead:
        read = VisaRead.model_validate(visa)
        read.client_name = client_name
        return read

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def create(
        self, payload: VisaCreate, *, actor_id: Optional[UUID] = None
    ) -> Visa:
        await self._ensure_client(payload.client_id)
        visa = Visa(
            **payload.model_dump(exclude={"status"}),
            status=payload.status.value,
            created_by=actor_id,
        )
        await self.repo.add(visa)
        if visa.status != VisaStatus.not_started.value:
            await self._record_history(
                visa, None, visa.status, actor_id, "Initial status"
            )
        return visa

    async def _record_history(
        self,
        visa: Visa,
        old_status: Optional[str],
        new_status: str,
        actor_id: Optional[UUID],
        note: Optional[str],
    ) -> None:
        self.session.add(
            VisaStatusHistory(
                visa_id=visa.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=actor_id,
                note=note,
            )
        )
        await self.session.flush()

    async def update(
        self,
        visa: Visa,
        payload: VisaUpdate,
        *,
        actor_id: Optional[UUID] = None,
    ) -> Visa:
        data = payload.model_dump(exclude_unset=True)
        status_note = data.pop("status_note", None)
        new_status = data.pop("status", None)
        if new_status is not None:
            new_status = new_status.value
            if new_status != visa.status:
                await self._record_history(
                    visa, visa.status, new_status, actor_id, status_note
                )
                if new_status == VisaStatus.approved.value and not visa.approval_date:
                    visa.approval_date = date.today()
                visa.status = new_status

        for key, value in data.items():
            setattr(visa, key, value)
        visa.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return visa

    async def delete(self, visa: Visa) -> None:
        await self.session.delete(visa)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        trip_id: Optional[UUID] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[VisaRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            trip_id=trip_id,
            status=status,
            q=q,
            page=page,
            page_size=page_size,
        )
        return [self.to_read(visa, name) for visa, name in rows], total

    async def detail(self, visa: Visa, client_name: Optional[str]) -> VisaDetail:
        base = self.to_read(visa, client_name)
        history = await self.repo.history(visa.id)
        return VisaDetail(
            **base.model_dump(),
            history=[VisaHistoryRead.model_validate(h) for h in history],
        )
