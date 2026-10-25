from __future__ import annotations

from sqlalchemy import Enum

from app.models.user import User


def test_user_role_enum_matches_migration_type() -> None:
    role_type = User.__table__.c.role.type
    assert isinstance(role_type, Enum)
    assert role_type.name == "user_role"
    assert role_type.schema == "crm"
    assert list(role_type.enums) == [
        "super_admin",
        "admin",
        "agent",
        "accountant",
        "read_only",
    ]
