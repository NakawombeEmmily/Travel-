"""phase3_feedback_crm

Revision ID: 0003_phase3_crm
Revises: 0002_phase2_crm_modules
Create Date: 2026-10-19

Phase 3: feedback, interactions, leads (pipeline), tags, client tags, follow-up tasks.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003_phase3_crm"
down_revision: Union[str, None] = "0002_phase2_crm_modules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("trip_id", sa.UUID(), nullable=True),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=True),
        sa.Column("sentiment", sa.String(length=20), server_default="neutral", nullable=False),
        sa.Column("feedback_date", sa.Date(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_feedback_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["crm.trips.id"], name="fk_feedback_trip_id_trips", ondelete="SET NULL"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
        schema="crm",
    )
    op.create_index("idx_feedback_client", "feedback", ["client_id"], schema="crm")
    op.create_index("idx_feedback_sentiment", "feedback", ["sentiment"], schema="crm")
    op.create_index("idx_feedback_date", "feedback", ["feedback_date"], schema="crm")

    op.create_table(
        "interactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("interaction_type", sa.String(length=20), server_default="other", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("contacted_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_interactions"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_interactions_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contacted_by"], ["crm.users.id"], name="fk_interactions_contacted_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_interactions_client", "interactions", ["client_id"], schema="crm")
    op.create_index("idx_interactions_follow_up", "interactions", ["follow_up_date"], schema="crm")

    op.create_table(
        "leads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="lead", nullable=False),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_leads"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_leads_client_id_clients", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["crm.users.id"], name="fk_leads_assigned_to_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_leads_status", "leads", ["status"], schema="crm")
    op.create_index("idx_leads_assigned", "leads", ["assigned_to"], schema="crm")

    op.create_table(
        "tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), server_default="#F97316", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("name", name="uq_tags_name"),
        schema="crm",
    )

    op.create_table(
        "client_tags",
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("client_id", "tag_id", name="pk_client_tags"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_client_tags_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["crm.tags.id"], name="fk_client_tags_tag_id_tags", ondelete="CASCADE"),
        schema="crm",
    )

    op.create_table(
        "follow_up_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("priority", sa.String(length=10), server_default="medium", nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_follow_up_tasks"),
        sa.ForeignKeyConstraint(["client_id"], ["crm.clients.id"], name="fk_follow_up_tasks_client_id_clients", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to"], ["crm.users.id"], name="fk_follow_up_tasks_assigned_to_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["crm.users.id"], name="fk_follow_up_tasks_created_by_users", ondelete="SET NULL"),
        schema="crm",
    )
    op.create_index("idx_tasks_client", "follow_up_tasks", ["client_id"], schema="crm")
    op.create_index("idx_tasks_status", "follow_up_tasks", ["status"], schema="crm")
    op.create_index("idx_tasks_due", "follow_up_tasks", ["due_date"], schema="crm")


def downgrade() -> None:
    op.drop_table("follow_up_tasks", schema="crm")
    op.drop_table("client_tags", schema="crm")
    op.drop_table("tags", schema="crm")
    op.drop_table("leads", schema="crm")
    op.drop_table("interactions", schema="crm")
    op.drop_table("feedback", schema="crm")
