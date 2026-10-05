import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.race import Race
    from app.models.user import User


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("user_id", "source", "external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(20), default="strava")
    external_id: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(300))
    sport_type: Mapped[str] = mapped_column(String(50))
    workout_type: Mapped[int | None] = mapped_column(Integer)
    race_candidate_status: Mapped[str] = mapped_column(String(20), default="pending")
    suggested_category: Mapped[str | None] = mapped_column(String(30))
    suggestion_confidence: Mapped[str | None] = mapped_column(String(20))
    suggestion_score: Mapped[int] = mapped_column(Integer, default=0)
    suggestion_reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    distance_meters: Mapped[float] = mapped_column(Float)
    moving_time_seconds: Mapped[int] = mapped_column(Integer)
    elapsed_time_seconds: Mapped[int] = mapped_column(Integer)
    elevation_gain: Mapped[float] = mapped_column(Float, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    timezone: Mapped[str | None] = mapped_column(String(100))
    start_latitude: Mapped[float | None] = mapped_column(Float)
    start_longitude: Mapped[float | None] = mapped_column(Float)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), index=True
    )
    summary_polyline: Mapped[str | None] = mapped_column(String)
    is_commute: Mapped[bool] = mapped_column(Boolean, default=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    source_visibility: Mapped[str] = mapped_column(String(30), default="private")
    local_visibility: Mapped[str] = mapped_column(String(20), default="private")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="activities")
    location: Mapped["Location | None"] = relationship(back_populates="activities")
    race: Mapped["Race | None"] = relationship(back_populates="activity")
