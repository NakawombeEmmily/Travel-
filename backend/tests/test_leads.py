from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_lead_pipeline(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/leads",
        json={
            "full_name": "Jane Prospect",
            "email": "jane@example.com",
            "phone": "+256700111222",
            "source": "referral",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    lead = create.json()
    assert lead["status"] == "lead"

    listing = await client.get("/api/v1/leads", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    filtered = await client.get(
        "/api/v1/leads?status=lead", headers=auth_headers
    )
    assert filtered.status_code == 200
    assert any(i["id"] == lead["id"] for i in filtered.json()["items"])

    update = await client.patch(
        f"/api/v1/leads/{lead['id']}",
        json={"status": "quote_sent"},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "quote_sent"

    delete = await client.delete(
        f"/api/v1/leads/{lead['id']}", headers=auth_headers
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_lead_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/leads")
    assert resp.status_code == 401
