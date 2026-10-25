from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.passwords import hash_password
from app.models.user import User, UserRole

PASSWORD = "UserPass123!"


async def _create_user(
    session: AsyncSession, *, email: str, role: UserRole
) -> User:
    existing = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        full_name=f"{role.value} user",
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _headers_for(client: AsyncClient, email: str) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_agent_cannot_manage_users(
    client: AsyncClient, session: AsyncSession
) -> None:
    agent = await _create_user(
        session, email="users.agent@example.com", role=UserRole.agent
    )
    headers = await _headers_for(client, agent.email)

    assert (await client.get("/api/v1/users", headers=headers)).status_code == 403
    resp = await client.patch(
        f"/api/v1/users/{agent.id}/role",
        headers=headers,
        json={"role": "admin"},
    )
    assert resp.status_code == 403


async def test_admin_can_promote_agent_to_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _create_user(
        session, email="users.manager@example.com", role=UserRole.admin
    )
    agent = await _create_user(
        session, email="users.promote@example.com", role=UserRole.agent
    )
    admin_headers = await _headers_for(client, admin.email)
    agent_headers = await _headers_for(client, agent.email)

    listing = await client.get("/api/v1/users", headers=admin_headers)
    assert listing.status_code == 200
    assert agent.email in {user["email"] for user in listing.json()}

    resp = await client.patch(
        f"/api/v1/users/{agent.id}/role",
        headers=admin_headers,
        json={"role": "admin"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "admin"

    await session.refresh(agent)
    assert agent.role == UserRole.admin

    analytics = await client.get(
        "/api/v1/analytics/summary", headers=agent_headers
    )
    assert analytics.status_code == 200, analytics.text


async def test_admin_cannot_assign_super_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _create_user(
        session, email="users.limited@example.com", role=UserRole.admin
    )
    agent = await _create_user(
        session, email="users.noescalate@example.com", role=UserRole.agent
    )
    headers = await _headers_for(client, admin.email)

    resp = await client.patch(
        f"/api/v1/users/{agent.id}/role",
        headers=headers,
        json={"role": "super_admin"},
    )
    assert resp.status_code == 403
    await session.refresh(agent)
    assert agent.role == UserRole.agent


async def test_admin_cannot_modify_super_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _create_user(
        session, email="users.mods@example.com", role=UserRole.admin
    )
    super_admin = await _create_user(
        session, email="users.owner@example.com", role=UserRole.super_admin
    )
    headers = await _headers_for(client, admin.email)

    resp = await client.patch(
        f"/api/v1/users/{super_admin.id}/role",
        headers=headers,
        json={"role": "agent"},
    )
    assert resp.status_code == 403
    await session.refresh(super_admin)
    assert super_admin.role == UserRole.super_admin


async def test_admin_cannot_change_own_role(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _create_user(
        session, email="users.self@example.com", role=UserRole.admin
    )
    headers = await _headers_for(client, admin.email)

    resp = await client.patch(
        f"/api/v1/users/{admin.id}/role",
        headers=headers,
        json={"role": "agent"},
    )
    assert resp.status_code == 400
    await session.refresh(admin)
    assert admin.role == UserRole.admin
