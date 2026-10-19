from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_crud_and_stats(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    create = await client.post(
        "/api/v1/tasks",
        json={
            "client_id": sample_client["id"],
            "title": "Confirm hotel booking",
            "description": "Call the Nairobi hotel",
            "due_date": "2026-11-20",
            "priority": "high",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    task = create.json()
    assert task["status"] == "pending"
    assert task["priority"] == "high"
    assert task["client_name"] == "Test Traveller"

    listing = await client.get("/api/v1/tasks", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    stats = await client.get("/api/v1/tasks/stats", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["open"] >= 1

    update = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "completed"

    delete = await client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_tasks_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 401
