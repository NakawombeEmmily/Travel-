from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.repositories.lead import LeadRepository
from app.schemas.lead import LeadCreate, LeadRead, LeadUpdate


class LeadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LeadRepository(session)

    def to_read(self, item: Lead) -> LeadRead:
        return LeadRead.model_validate(item)

    async def create(
        self, payload: LeadCreate, *, actor_id: Optional[UUID] = None
    ) -> Lead:
        item = Lead(
            **payload.model_dump(exclude={"status"}),
            status=payload.status.value,
        )
        await self.repo.add(item)
        return item

    async def update(self, item: Lead, payload: LeadUpdate) -> Lead:
        data = payload.model_dump(exclude_unset=True)
        if data.get("status") is not None:
            data["status"] = data["status"].value
        for key, value in data.items():
            setattr(item, key, value)
        await self.session.flush()
        return item

    async def delete(self, item: Lead) -> None:
        await self.session.delete(item)

    async def search(
        self,
        *,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[LeadRead], int]:
        rows, total = await self.repo.search(
            status=status, q=q, page=page, page_size=page_size
        )
        return [self.to_read(item) for item in rows], total
