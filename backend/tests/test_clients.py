from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security.encryption import EncryptionService


def _payload(passport: str = "CM1234567", **overrides) -> dict:
    data = {
        "full_name": "Jane Traveller",
        "date_of_birth": "1990-05-10",
        "gender": "female",
        "email": "jane@example.com",
        "phone": "+256700000000",
        "address": "Kampala, Uganda",
        "passport_number": passport,
        "passport_issue_date": "2020-01-01",
        "passport_expiry_date": "2030-01-01",
        "issuing_country": "Uganda",
        "nationality": "Ugandan",
        "emergency_contact": "+256711111111",
        "consent_given": True,
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_client_encrypts_passport(
    client: AsyncClient, auth_headers, session
) -> None:
    resp = await client.post(
        "/api/v1/clients", json=_payload(), headers=auth_headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["passport_number_masked"].endswith("4567")
    assert body["passport_number_masked"].count("*") >= 3
    assert "passport_number" not in body

    from uuid import UUID

    from sqlalchemy import select

    from app.models.client import Client

    row = (
        await session.execute(
            select(Client).where(Client.id == UUID(body["id"]))
        )
    ).scalar_one()
    enc = EncryptionService(settings.ENCRYPTION_KEY)
    assert enc.decrypt(row.passport_number_enc) == "CM1234567"
    assert row.passport_number_hash == enc.hash_plaintext("CM1234567")


@pytest.mark.asyncio
async def test_duplicate_passport_rejected(
    client: AsyncClient, auth_headers
) -> None:
    await client.post(
        "/api/v1/clients", json=_payload("DUP0001"), headers=auth_headers
    )
    resp = await client.post(
        "/api/v1/clients", json=_payload("DUP0001"), headers=auth_headers
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_reveal_passport_logs_audit(
    client: AsyncClient, auth_headers, session
) -> None:
    created = await client.post(
        "/api/v1/clients", json=_payload("REV0001"), headers=auth_headers
    )
    cid = created.json()["id"]
    resp = await client.post(
        f"/api/v1/clients/{cid}/reveal", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["passport_number"] == "REV0001"

    from sqlalchemy import select

    from app.models.audit import AuditLog

    rows = (
        await session.execute(
            select(AuditLog).where(AuditLog.action == "reveal")
        )
    ).scalars().all()
    assert any(str(r.entity_id) == cid for r in rows)


@pytest.mark.asyncio
async def test_search_and_pagination(
    client: AsyncClient, auth_headers
) -> None:
    await client.post(
        "/api/v1/clients",
        json=_payload("SRCH001", full_name="Alice Wander"),
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/clients",
        json=_payload("SRCH002", full_name="Bob Roam", nationality="Kenyan"),
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/clients?q=Alice&page=1&page_size=10",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all("Alice" in i["full_name"] for i in body["items"])


@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient, auth_headers) -> None:
    created = await client.post(
        "/api/v1/clients", json=_payload("DEL0001"), headers=auth_headers
    )
    cid = created.json()["id"]
    resp = await client.delete(
        f"/api/v1/clients/{cid}", headers=auth_headers
    )
    assert resp.status_code == 204
    resp = await client.get(
        f"/api/v1/clients/{cid}", headers=auth_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_passport_expiring_flag(
    client: AsyncClient, auth_headers
) -> None:
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta

    expiring = (date.today() + relativedelta(months=3)).isoformat()
    resp = await client.post(
        "/api/v1/clients",
        json=_payload(
            "EXP0001",
            passport_expiry_date=expiring,
            passport_issue_date="2015-01-01",
        ),
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["passport_expiring_soon"] is True
    _ = timedelta
