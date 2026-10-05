import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.medal import Medal
    from app.models.user import User


class Race(Base):
    __tablename__ = "races"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activities.id", ondelete="SET NULL"), unique=True
    )
    event_name: Mapped[str] = mapped_column(String(300))
    race_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(30))
    official_distance_meters: Mapped[float] = mapped_column(Float)
    recorded_distance_meters: Mapped[float | None] = mapped_column(Float)
    net_time_seconds: Mapped[int | None] = mapped_column(Integer)
    gross_time_seconds: Mapped[int | None] = mapped_column(Integer)
    bib_number: Mapped[str | None] = mapped_column(String(30))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2), default="BR")
    result_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(20), default="private")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="races")
    activity: Mapped["Activity | None"] = relationship(back_populates="race")
    medal: Mapped["Medal | None"] = relationship(
        back_populates="race", cascade="all, delete-orphan"
    )
