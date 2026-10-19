from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_interaction_crud(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    create = await client.post(
        "/api/v1/interactions",
        json={
            "client_id": sample_client["id"],
            "interaction_type": "call",
            "notes": "Discussed Nairobi itinerary",
            "follow_up_date": "2026-11-05",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    item = create.json()
    assert item["interaction_type"] == "call"
    assert item["client_name"] == "Test Traveller"

    listing = await client.get(
        "/api/v1/interactions", headers=auth_headers
    )
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    update = await client.patch(
        f"/api/v1/interactions/{item['id']}",
        json={"interaction_type": "meeting"},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()["interaction_type"] == "meeting"

    delete = await client.delete(
        f"/api/v1/interactions/{item['id']}", headers=auth_headers
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_interaction_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/interactions")
    assert resp.status_code == 401
