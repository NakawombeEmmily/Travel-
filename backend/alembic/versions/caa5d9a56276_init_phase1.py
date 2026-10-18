"""init_phase1

Revision ID: 0001_init_phase1
Revises:
Create Date: 2026-10-18

Phase 1: schemas crm/admin, core enums, users, audit_log, clients.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001_init_phase1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS crm")
    op.execute("CREATE SCHEMA IF NOT EXISTS admin")

    user_role = sa.Enum(
        "super_admin", "admin", "agent", "accountant", "read_only",
        name="user_role", schema="crm",
    )
    user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum(name="user_role", schema="crm", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assigned_clients_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.ForeignKeyConstraint(['created_by'], ['crm.users.id'], name='fk_users_created_by_users', ondelete='SET NULL'),
        schema='crm'
    )
    op.create_index('idx_users_role', 'users', ['role'], schema='crm')
    op.create_index('idx_users_active', 'users', ['is_active'], schema='crm')

    op.create_table('audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_audit_log'),
        sa.ForeignKeyConstraint(['actor_id'], ['crm.users.id'], name='fk_audit_log_actor_id_users', ondelete='SET NULL'),
        schema='crm'
    )
    op.create_index('idx_audit_actor', 'audit_log', ['actor_id'], schema='crm')
    op.create_index('idx_audit_entity', 'audit_log', ['entity_type', 'entity_id'], schema='crm')
    op.create_index('idx_audit_created', 'audit_log', ['created_at'], schema='crm')
    op.create_index('idx_audit_action', 'audit_log', ['action'], schema='crm')

    op.create_table('clients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('passport_number_enc', sa.LargeBinary(), nullable=False),
        sa.Column('passport_number_hash', sa.String(length=64), nullable=False),
        sa.Column('passport_issue_date', sa.Date(), nullable=True),
        sa.Column('passport_expiry_date', sa.Date(), nullable=True),
        sa.Column('issuing_country', sa.String(length=100), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact', sa.String(length=255), nullable=True),
        sa.Column('consent_given', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_retention_until', sa.Date(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_clients'),
        sa.UniqueConstraint('passport_number_hash', name='uq_clients_passport_number_hash'),
        sa.ForeignKeyConstraint(['created_by'], ['crm.users.id'], name='fk_clients_created_by_users', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['crm.users.id'], name='fk_clients_updated_by_users', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['crm.users.id'], name='fk_clients_deleted_by_users', ondelete='SET NULL'),
        schema='crm'
    )
    op.create_index('idx_clients_email', 'clients', ['email'], schema='crm')
    op.create_index('idx_clients_nationality', 'clients', ['nationality'], schema='crm')
    op.create_index('idx_clients_deleted', 'clients', ['is_deleted'], schema='crm')
    op.create_index('idx_clients_created', 'clients', ['created_at'], schema='crm')
    op.create_index('idx_clients_expiry', 'clients', ['passport_expiry_date'], schema='crm')


def downgrade() -> None:
    op.drop_table('clients', schema='crm')
    op.drop_table('audit_log', schema='crm')
    op.drop_table('users', schema='crm')
    op.execute('DROP TYPE IF EXISTS crm.user_role')
    op.execute('DROP SCHEMA IF EXISTS crm CASCADE')
    op.execute('DROP SCHEMA IF EXISTS admin CASCADE')
