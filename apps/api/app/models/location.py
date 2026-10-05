import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.activity import Activity


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("latitude_bucket", "longitude_bucket"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude_bucket: Mapped[float] = mapped_column(Float)
    longitude_bucket: Mapped[float] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(150))
    state: Mapped[str | None] = mapped_column(String(150))
    country: Mapped[str] = mapped_column(String(150))
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    display_latitude: Mapped[float] = mapped_column(Float)
    display_longitude: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    activities: Mapped[list["Activity"]] = relationship(back_populates="location")
