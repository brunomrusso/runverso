"""Add race suggestions and races.

Revision ID: 20261004_0004
Revises: 20261004_0003
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0004"
down_revision: str | None = "20261004_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("workout_type", sa.Integer()))
    op.add_column(
        "activities",
        sa.Column("race_candidate_status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column("activities", sa.Column("suggested_category", sa.String(30)))
    op.add_column("activities", sa.Column("suggestion_confidence", sa.String(20)))
    op.add_column(
        "activities",
        sa.Column("suggestion_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "activities",
        sa.Column(
            "suggestion_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.execute(
        "UPDATE activities SET workout_type = CASE "
        "WHEN raw_payload->>'workout_type' ~ '^[0-9]+$' "
        "THEN (raw_payload->>'workout_type')::integer ELSE NULL END"
    )
    op.create_table(
        "races",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_name", sa.String(300), nullable=False),
        sa.Column("race_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("official_distance_meters", sa.Float(), nullable=False),
        sa.Column("recorded_distance_meters", sa.Float()),
        sa.Column("net_time_seconds", sa.Integer()),
        sa.Column("gross_time_seconds", sa.Integer()),
        sa.Column("bib_number", sa.String(30)),
        sa.Column("city", sa.String(120)),
        sa.Column("state", sa.String(120)),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("result_url", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id"),
    )
    op.create_index(op.f("ix_races_user_id"), "races", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_races_user_id"), table_name="races")
    op.drop_table("races")
    op.drop_column("activities", "suggestion_reasons")
    op.drop_column("activities", "suggestion_score")
    op.drop_column("activities", "suggestion_confidence")
    op.drop_column("activities", "suggested_category")
    op.drop_column("activities", "race_candidate_status")
    op.drop_column("activities", "workout_type")
