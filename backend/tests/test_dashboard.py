from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["active_clients"] >= 1
    assert "trips_by_status" in body
    assert "visas_by_status" in body
    assert "upcoming_departures" in body
    assert float(body["revenue_mtd"]) == 0.0


@pytest.mark.asyncio
async def test_reminders_preview(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get("/api/v1/reminders/preview", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "passports" in body
    assert "visas" in body


@pytest.mark.asyncio
async def test_reminders_run_requires_admin(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post("/api/v1/reminders/run", headers=auth_headers)
    assert resp.status_code == 200
    assert "sent" in resp.json()
