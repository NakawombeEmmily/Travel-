from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"healthy", "degraded"}
    assert body["environment"] == "test"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient, admin_user) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient, auth_headers) -> None:
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "super_admin"


@pytest.mark.asyncio
async def test_register_creates_account_and_logs_in(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newagent@example.com",
            "full_name": "New Agent",
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    profile = me.json()
    assert profile["email"] == "newagent@example.com"
    assert profile["role"] == "agent"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, admin_user) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_user.email,
            "full_name": "Duplicate",
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_rejects_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "full_name": "Short Pass",
            "password": "short",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient, admin_user) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"},
    )
    refresh_token = login.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
