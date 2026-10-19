from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.encryption import EncryptionService
from app.models.client import Client
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.utils.masking import mask_passport, passport_expiring_soon


class DuplicatePassportError(Exception):
    pass


class ClientService:
    def __init__(
        self, session: AsyncSession, encryption: EncryptionService
    ) -> None:
        self.repo = ClientRepository(session)
        self.encryption = encryption

    def _masked(self, client: Client) -> str:
        try:
            plaintext = self.encryption.decrypt(client.passport_number_enc)
        except Exception:  # pragma: no cover - defensive
            return "******"
        return mask_passport(plaintext)

    def to_read(self, client: Client) -> ClientRead:
        return ClientRead(
            id=client.id,
            full_name=client.full_name,
            date_of_birth=client.date_of_birth,
            gender=client.gender,
            email=client.email,
            phone=client.phone,
            address=client.address,
            passport_issue_date=client.passport_issue_date,
            passport_expiry_date=client.passport_expiry_date,
            issuing_country=client.issuing_country,
            nationality=client.nationality,
            emergency_contact=client.emergency_contact,
            consent_given=client.consent_given,
            data_retention_until=client.data_retention_until,
            passport_number_masked=self._masked(client),
            passport_expiring_soon=passport_expiring_soon(
                client.passport_expiry_date
            ),
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    async def create(
        self,
        payload: ClientCreate,
        *,
        actor_id: Optional[UUID] = None,
    ) -> Client:
        passport_hash = self.encryption.hash_plaintext(payload.passport_number)
        existing = await self.repo.get_by_passport_hash(passport_hash)
        if existing is not None:
            raise DuplicatePassportError(payload.passport_number)

        data = payload.model_dump(exclude={"passport_number"})
        client = Client(
            **data,
            passport_number_enc=self.encryption.encrypt(
                payload.passport_number
            ),
            passport_number_hash=passport_hash,
            created_by=actor_id,
            updated_by=actor_id,
        )
        if payload.consent_given:
            client.consent_date = datetime.now(UTC)
        await self.repo.add(client)
        return client

    async def update(
        self,
        client: Client,
        payload: ClientUpdate,
        *,
        actor_id: Optional[UUID] = None,
    ) -> Client:
        data = payload.model_dump(exclude_unset=True)
        passport_number = data.pop("passport_number", None)

        if passport_number is not None:
            new_hash = self.encryption.hash_plaintext(passport_number)
            if new_hash != client.passport_number_hash:
                existing = await self.repo.get_by_passport_hash(new_hash)
                if existing is not None and existing.id != client.id:
                    raise DuplicatePassportError(passport_number)
                client.passport_number_enc = self.encryption.encrypt(
                    passport_number
                )
                client.passport_number_hash = new_hash

        for key, value in data.items():
            setattr(client, key, value)

        if payload.consent_given and client.consent_date is None:
            client.consent_date = datetime.now(UTC)

        client.updated_by = actor_id
        client.updated_at = datetime.now(UTC)
        await self.repo.session.flush()
        return client

    async def reveal_passport(self, client: Client) -> str:
        return self.encryption.decrypt(client.passport_number_enc)

    async def search(
        self,
        *,
        q: Optional[str] = None,
        nationality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> tuple[list[ClientRead], int]:
        rows, total = await self.repo.search(
            q=q,
            nationality=nationality,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted,
        )
        return [self.to_read(row) for row in rows], total

    async def soft_delete(
        self, client: Client, *, actor_id: Optional[UUID] = None
    ) -> None:
        client.is_deleted = True
        client.deleted_at = datetime.now(UTC)
        client.deleted_by = actor_id
        await self.repo.session.flush()


__all__ = ["ClientService", "DuplicatePassportError"]
