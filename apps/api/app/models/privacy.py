import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PrivacySettings(Base):
    __tablename__ = "privacy_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    profile_visibility: Mapped[str] = mapped_column(String(20), default="public")
    activities_visibility: Mapped[str] = mapped_column(String(20), default="private")
    races_visibility: Mapped[str] = mapped_column(String(20), default="public")
    medals_visibility: Mapped[str] = mapped_column(String(20), default="public")
    photos_visibility: Mapped[str] = mapped_column(String(20), default="followers")
    locations_visibility: Mapped[str] = mapped_column(String(20), default="followers")
    show_real_name: Mapped[bool] = mapped_column(Boolean, default=False)
    show_times: Mapped[bool] = mapped_column(Boolean, default=True)
    approve_followers: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="privacy_settings")
