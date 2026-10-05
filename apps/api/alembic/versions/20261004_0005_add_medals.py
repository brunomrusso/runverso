"""Add medals and private photos.

Revision ID: 20261004_0005
Revises: 20261004_0004
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0005"
down_revision: str | None = "20261004_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("race_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("story", sa.Text()),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("race_id"),
    )
    op.create_index(op.f("ix_medals_user_id"), "medals", ["user_id"])
    op.create_table(
        "medal_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("thumbnail_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["medal_id"], ["medals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medal_photos_medal_id"), "medal_photos", ["medal_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_medal_photos_medal_id"), table_name="medal_photos")
    op.drop_table("medal_photos")
    op.drop_index(op.f("ix_medals_user_id"), table_name="medals")
    op.drop_table("medals")
