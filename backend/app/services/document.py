from __future__ import annotations

import hashlib
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.encryption import EncryptionService
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.services.storage import LocalStorage


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        encryption: EncryptionService,
        storage: LocalStorage,
    ) -> None:
        self.session = session
        self.encryption = encryption
        self.storage = storage
        self.repo = DocumentRepository(session)

    async def upload(
        self,
        *,
        data: bytes,
        filename: str,
        content_type: Optional[str],
        client_id: Optional[UUID],
        visa_id: Optional[UUID],
        actor_id: Optional[UUID] = None,
    ) -> Document:
        checksum = hashlib.sha256(data).hexdigest()
        key = f"documents/{uuid4().hex}"
        self.storage.save(key, self.encryption.encrypt_bytes(data))
        document = Document(
            client_id=client_id,
            visa_id=visa_id,
            file_key=key,
            original_filename=filename,
            file_type=content_type,
            file_size=len(data),
            is_encrypted=True,
            uploaded_by=actor_id,
            checksum=checksum,
        )
        await self.repo.add(document)
        return document

    async def list(
        self,
        *,
        client_id: Optional[UUID] = None,
        visa_id: Optional[UUID] = None,
    ) -> list[Document]:
        return await self.repo.list_by(client_id=client_id, visa_id=visa_id)

    async def read(self, document_id: UUID) -> tuple[Document, bytes]:
        document = await self.repo.get(document_id)
        if document is None:
            raise DocumentNotFoundError(str(document_id))
        raw = self.storage.read(document.file_key)
        data = (
            self.encryption.decrypt_bytes(raw)
            if document.is_encrypted
            else raw
        )
        return document, data

    async def delete(self, document_id: UUID) -> None:
        document = await self.repo.get(document_id)
        if document is None:
            raise DocumentNotFoundError(str(document_id))
        self.storage.delete(document.file_key)
        await self.session.delete(document)
