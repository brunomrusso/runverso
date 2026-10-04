"""Add identity, profile, privacy and session tables.

Revision ID: 20261004_0002
Revises: 20261004_0001
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0002"
down_revision: str | None = "20261004_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=True),
        sa.Column("real_name", sa.String(length=120), nullable=True),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("started_running_year", sa.Integer(), nullable=True),
        sa.Column("favorite_distance", sa.String(length=30), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(op.f("ix_profiles_username"), "profiles", ["username"], unique=True)
    op.create_table(
        "privacy_settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_visibility", sa.String(length=20), nullable=False),
        sa.Column("activities_visibility", sa.String(length=20), nullable=False),
        sa.Column("races_visibility", sa.String(length=20), nullable=False),
        sa.Column("medals_visibility", sa.String(length=20), nullable=False),
        sa.Column("photos_visibility", sa.String(length=20), nullable=False),
        sa.Column("locations_visibility", sa.String(length=20), nullable=False),
        sa.Column("show_real_name", sa.Boolean(), nullable=False),
        sa.Column("show_times", sa.Boolean(), nullable=False),
        sa.Column("approve_followers", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "auth_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id"),
    )
    op.create_index(op.f("ix_auth_identities_user_id"), "auth_identities", ["user_id"])
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_table(
        "strava_connections",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("athlete_id", sa.String(length=100), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.String(length=200), nullable=False),
        sa.Column("sync_status", sa.String(length=20), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("athlete_id"),
    )


def downgrade() -> None:
    op.drop_table("strava_connections")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(op.f("ix_auth_identities_user_id"), table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_table("privacy_settings")
    op.drop_index(op.f("ix_profiles_username"), table_name="profiles")
    op.drop_table("profiles")
