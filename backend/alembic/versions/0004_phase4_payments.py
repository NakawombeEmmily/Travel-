"""phase4_payments_outbox_admin

Revision ID: 0004_phase4_payments
Revises: 0003_phase3_crm
Create Date: 2026-10-19

Phase 4: payments (+ installments, transactional outbox) and the admin
ledger, invoices and revenue summary tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_phase4_payments"
down_revision: Union[str, None] = "0003_phase3_crm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS admin")

    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("trip_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("exchange_rate", sa.Numeric(12, 6), server_default="1.0", nullable=False),
        sa.Column("method", sa.String(length=20), server_default="cash", nullable=False),
        sa.Column("provider", sa.String(length=30), server_default="mock", nullable=False),
        sa.Column("provider_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.UniqueConstraint("invoice_number", name="uq_payments_invoice_number"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_payments_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["crm.trips.id"], name="fk_payments_trip_id_trips", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["crm.users.id"], name="fk_payments_created_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_payments_client", "payments", ["client_id"], schema="crm")
    op.create_index("idx_payments_trip", "payments", ["trip_id"], schema="crm")
    op.create_index("idx_payments_status", "payments", ["status"], schema="crm")
    op.create_index("idx_payments_invoice", "payments", ["invoice_number"], schema="crm")
    op.create_index("idx_payments_provider_tx", "payments", ["provider_transaction_id"], schema="crm")

    op.create_table(
        "payment_installments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_payment_installments"),
        sa.ForeignKeyConstraint(["payment_id"], ["crm.payments.id"], name="fk_payment_installments_payment_id_payments", ondelete="CASCADE"),
        schema="crm",
    )
    op.create_index("idx_payment_installments_payment", "payment_installments", ["payment_id"], schema="crm")
    op.create_index("idx_payment_installments_status", "payment_installments", ["status"], schema="crm")
    op.create_index("idx_payment_installments_due", "payment_installments", ["due_date"], schema="crm")

    op.create_table(
        "payment_outbox",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("aggregate_type", sa.String(length=50), server_default="payment", nullable=False),
        sa.Column("aggregate_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="10", nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_payment_outbox"),
        sa.UniqueConstraint("event_id", name="uq_payment_outbox_event_id"),
        schema="crm",
    )
    op.create_index("idx_payment_outbox_status", "payment_outbox", ["status"], schema="crm")
    op.create_index("idx_payment_outbox_next_attempt", "payment_outbox", ["next_attempt_at"], schema="crm")
    op.create_index("idx_payment_outbox_aggregate", "payment_outbox", ["aggregate_id"], schema="crm")
    op.create_index("idx_payment_outbox_event", "payment_outbox", ["event_id"], schema="crm")

    op.create_table(
        "admin_ledger",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("crm_payment_id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=True),
        sa.Column("trip_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=True),
        sa.Column("provider_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_admin_ledger"),
        sa.UniqueConstraint("crm_payment_id", name="uq_admin_ledger_crm_payment_id"),
        schema="admin",
    )
    op.create_index("idx_admin_ledger_status", "admin_ledger", ["status"], schema="admin")
    op.create_index("idx_admin_ledger_invoice", "admin_ledger", ["invoice_number"], schema="admin")

    op.create_table(
        "admin_invoices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ledger_id", sa.UUID(), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("issue_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("pdf_key", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_admin_invoices"),
        sa.ForeignKeyConstraint(["ledger_id"], ["admin.admin_ledger.id"], name="fk_admin_invoices_ledger_id_admin_ledger", ondelete="CASCADE"),
        schema="admin",
    )
    op.create_index("idx_admin_invoices_invoice", "admin_invoices", ["invoice_number"], schema="admin")
    op.create_index("idx_admin_invoices_status", "admin_invoices", ["status"], schema="admin")

    op.create_table(
        "admin_revenue_summary",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("summary_date", sa.Date(), nullable=False),
        sa.Column("period_type", sa.String(length=10), nullable=False),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("transaction_count", sa.Integer(), nullable=False),
        sa.Column("completed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("refunded_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_admin_revenue_summary"),
        sa.UniqueConstraint("summary_date", "period_type", "currency", name="uq_revenue_summary_date_period_currency"),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_table("admin_revenue_summary", schema="admin")
    op.drop_table("admin_invoices", schema="admin")
    op.drop_table("admin_ledger", schema="admin")
    op.drop_table("payment_outbox", schema="crm")
    op.drop_table("payment_installments", schema="crm")
    op.drop_table("payments", schema="crm")
