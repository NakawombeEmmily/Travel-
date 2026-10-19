from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by(
        self,
        *,
        client_id: Optional[UUID] = None,
        visa_id: Optional[UUID] = None,
    ) -> list[Document]:
        stmt = select(Document)
        if client_id:
            stmt = stmt.where(Document.client_id == client_id)
        if visa_id:
            stmt = stmt.where(Document.visa_id == visa_id)
        stmt = stmt.order_by(Document.uploaded_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
