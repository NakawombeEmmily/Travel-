"""Seed dev/staging only. Never run against production."""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
)

from app.core.config import settings
from app.core.security.encryption import EncryptionService
from app.core.security.passwords import hash_password
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.user import User, UserRole
from sqlalchemy import select


async def seed() -> None:
    if settings.ENVIRONMENT not in ("development", "dev", "staging", "test"):
        raise SystemExit(f"Refusing to seed ENVIRONMENT={settings.ENVIRONMENT}")

    enc = EncryptionService(settings.ENCRYPTION_KEY)
    async with SessionLocal() as session:
        existing = (
            await session.execute(
                select(User).where(User.email == "admin@example.com")
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                User(
                    email="admin@example.com",
                    password_hash=hash_password("Admin123!"),
                    full_name="Seed Admin",
                    role=UserRole.super_admin,
                    is_active=True,
                )
            )
        sample = [
            ("Amina Nakato", "UG", "CM1234567"),
            ("John Banda", "KE", "KE9876543"),
            ("Sarah Otieno", "TZ", "TZ4567890"),
        ]
        for name, nat, passport in sample:
            ph = enc.hash_plaintext(passport)
            found = (
                await session.execute(
                    select(Client).where(Client.passport_number_hash == ph)
                )
            ).scalar_one_or_none()
            if found is None:
                session.add(
                    Client(
                        full_name=name,
                        nationality=nat,
                        email=f"{name.split()[0].lower()}@example.com",
                        passport_number_enc=enc.encrypt(passport),
                        passport_number_hash=ph,
                        passport_expiry_date=date(2030, 1, 1),
                        issuing_country=nat,
                        consent_given=True,
                    )
                )
        await session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
