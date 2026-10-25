from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.passwords import hash_password
from app.models.user import User, UserRole

PASSWORD = "RolePass123!"


async def _headers_for(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    role: UserRole,
) -> dict[str, str]:
    existing = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            User(
                email=email,
                password_hash=hash_password(PASSWORD),
                full_name=f"{role.value} user",
                role=role,
                is_active=True,
            )
        )
        await session.commit()
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_agent_cannot_access_payments(
    client: AsyncClient, session: AsyncSession, sample_client: dict
) -> None:
    headers = await _headers_for(
        client, session, email="agent@example.com", role=UserRole.agent
    )
    assert (await client.get("/api/v1/payments", headers=headers)).status_code == 403
    assert (
        await client.get("/api/v1/payments/stats", headers=headers)
    ).status_code == 403
    resp = await client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "client_id": sample_client["id"],
            "amount": "10.00",
            "currency": "USD",
            "method": "cash",
        },
    )
    assert resp.status_code == 403


async def test_agent_cannot_access_analytics(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _headers_for(
        client, session, email="agent@example.com", role=UserRole.agent
    )
    paths = [
        "/api/v1/analytics/summary",
        "/api/v1/analytics/trends",
        "/api/v1/analytics/nationalities",
        "/api/v1/analytics/revenue",
        "/api/v1/analytics/export/clients",
    ]
    for path in paths:
        assert (await client.get(path, headers=headers)).status_code == 403


async def test_accountant_keeps_payments_but_not_analytics(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _headers_for(
        client, session, email="accountant@example.com", role=UserRole.accountant
    )
    assert (await client.get("/api/v1/payments", headers=headers)).status_code == 200
    assert (
        await client.get("/api/v1/analytics/summary", headers=headers)
    ).status_code == 403
