from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trip_crud(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    create = await client.post(
        "/api/v1/trips",
        json={
            "client_id": sample_client["id"],
            "destination_country": "Kenya",
            "travel_start_date": "2026-11-01",
            "travel_end_date": "2026-11-10",
            "purpose": "tourism",
            "total_cost": "1500.00",
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    trip = create.json()
    assert trip["destination_country"] == "Kenya"
    assert trip["client_name"] == "Test Traveller"
    assert trip["status"] == "inquiry"

    listing = await client.get("/api/v1/trips", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    update = await client.patch(
        f"/api/v1/trips/{trip['id']}",
        json={"status": "confirmed", "total_cost": "1600.00"},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "confirmed"

    got = await client.get(f"/api/v1/trips/{trip['id']}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["id"] == trip["id"]

    delete = await client.delete(f"/api/v1/trips/{trip['id']}", headers=auth_headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_trip_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/trips")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_trip_unknown_client(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/trips",
        json={
            "client_id": "00000000-0000-0000-0000-000000000000",
            "destination_country": "Nowhere",
            "travel_start_date": "2026-11-01",
            "total_cost": "0",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
