"""Add cached geographic locations.

Revision ID: 20261004_0006
Revises: 20261004_0005
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0006"
down_revision: str | None = "20261004_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latitude_bucket", sa.Float(), nullable=False),
        sa.Column("longitude_bucket", sa.Float(), nullable=False),
        sa.Column("city", sa.String(150)),
        sa.Column("state", sa.String(150)),
        sa.Column("country", sa.String(150), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("display_latitude", sa.Float(), nullable=False),
        sa.Column("display_longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("latitude_bucket", "longitude_bucket"),
    )
    op.create_index(op.f("ix_locations_country_code"), "locations", ["country_code"])
    op.add_column(
        "activities", sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_activities_location_id",
        "activities",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_activities_location_id"), "activities", ["location_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_activities_location_id"), table_name="activities")
    op.drop_constraint("fk_activities_location_id", "activities", type_="foreignkey")
    op.drop_column("activities", "location_id")
    op.drop_index(op.f("ix_locations_country_code"), table_name="locations")
    op.drop_table("locations")
