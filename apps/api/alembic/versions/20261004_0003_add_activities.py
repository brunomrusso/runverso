"""Add activities and sync metadata.

Revision ID: 20261004_0003
Revises: 20261004_0002
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0003"
down_revision: str | None = "20261004_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("strava_connections", sa.Column("sync_error", sa.String(500)))
    op.add_column(
        "strava_connections",
        sa.Column("imported_activities", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("sport_type", sa.String(50), nullable=False),
        sa.Column("distance_meters", sa.Float(), nullable=False),
        sa.Column("moving_time_seconds", sa.Integer(), nullable=False),
        sa.Column("elapsed_time_seconds", sa.Integer(), nullable=False),
        sa.Column("elevation_gain", sa.Float(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(100)),
        sa.Column("start_latitude", sa.Float()),
        sa.Column("start_longitude", sa.Float()),
        sa.Column("summary_polyline", sa.String()),
        sa.Column("is_commute", sa.Boolean(), nullable=False),
        sa.Column("is_manual", sa.Boolean(), nullable=False),
        sa.Column("source_visibility", sa.String(30), nullable=False),
        sa.Column("local_visibility", sa.String(20), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source", "external_id"),
    )
    op.create_index(op.f("ix_activities_user_id"), "activities", ["user_id"])
    op.create_index(op.f("ix_activities_started_at"), "activities", ["started_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_activities_started_at"), table_name="activities")
    op.drop_index(op.f("ix_activities_user_id"), table_name="activities")
    op.drop_table("activities")
    op.drop_column("strava_connections", "imported_activities")
    op.drop_column("strava_connections", "sync_error")
