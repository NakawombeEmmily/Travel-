"""phase2_trips_visas_documents

Revision ID: 0002_phase2_crm_modules
Revises: 0001_init_phase1
Create Date: 2026-10-19

Phase 2: trips, visas (+ status history), documents.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_phase2_crm_modules"
down_revision: Union[str, None] = "0001_init_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("destination_country", sa.String(length=100), nullable=False),
        sa.Column("travel_start_date", sa.Date(), nullable=False),
        sa.Column("travel_end_date", sa.Date(), nullable=True),
        sa.Column("purpose", sa.String(length=50), server_default="tourism", nullable=False),
        sa.Column("itinerary_notes", sa.Text(), nullable=True),
        sa.Column("total_cost", sa.Numeric(15, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="inquiry", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_trips"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_trips_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["crm.users.id"], name="fk_trips_created_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_trips_client", "trips", ["client_id"], schema="crm")
    op.create_index("idx_trips_status", "trips", ["status"], schema="crm")
    op.create_index("idx_trips_start", "trips", ["travel_start_date"], schema="crm")

    op.create_table(
        "visas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("trip_id", sa.UUID(), nullable=True),
        sa.Column("destination_country", sa.String(length=100), nullable=False),
        sa.Column("visa_type", sa.String(length=100), nullable=True),
        sa.Column("application_date", sa.Date(), nullable=True),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="not_started", nullable=False),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_visas"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_visas_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["crm.trips.id"], name="fk_visas_trip_id_trips", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["crm.users.id"], name="fk_visas_created_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_visas_client", "visas", ["client_id"], schema="crm")
    op.create_index("idx_visas_trip", "visas", ["trip_id"], schema="crm")
    op.create_index("idx_visas_status", "visas", ["status"], schema="crm")
    op.create_index("idx_visas_expiry", "visas", ["expiry_date"], schema="crm")

    op.create_table(
        "visa_status_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visa_id", sa.UUID(), nullable=False),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_visa_status_history"),
        sa.ForeignKeyConstraint(["visa_id"], ["crm.visas.id"], name="fk_visa_status_history_visa_id_visas", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["crm.users.id"], name="fk_visa_status_history_changed_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_visa_history_visa", "visa_status_history", ["visa_id"], schema="crm")

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=True),
        sa.Column("visa_id", sa.UUID(), nullable=True),
        sa.Column("file_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_documents_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visa_id"], ["crm.visas.id"], name="fk_documents_visa_id_visas", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["crm.users.id"], name="fk_documents_uploaded_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_documents_client", "documents", ["client_id"], schema="crm")
    op.create_index("idx_documents_visa", "documents", ["visa_id"], schema="crm")


def downgrade() -> None:
    op.drop_table("documents", schema="crm")
    op.drop_table("visa_status_history", schema="crm")
    op.drop_table("visas", schema="crm")
    op.drop_table("trips", schema="crm")
