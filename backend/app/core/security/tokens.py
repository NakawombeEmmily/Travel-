from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Optional, cast

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return cast(str, jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM))


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=7))
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "exp": expire,
    }
    return cast(
        str, jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=ALGORITHM)
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM]),
    )


def decode_refresh_token(token: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[ALGORITHM]),
    )


__all__ = [
    "ALGORITHM",
    "JWTError",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
]
