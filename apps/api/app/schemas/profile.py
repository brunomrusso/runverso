import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Visibility = Literal["public", "followers", "private"]


class ProfileUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    real_name: str | None = Field(default=None, max_length=120)
    display_name: str = Field(min_length=2, max_length=80)
    bio: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    started_running_year: int | None = Field(default=None, ge=1900, le=datetime.now().year)
    favorite_distance: str | None = Field(default=None, max_length=30)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]+", normalized):
            raise ValueError("Use apenas letras minúsculas, números e underline")
        return normalized

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str | None
    real_name: str | None
    display_name: str | None
    bio: str | None
    avatar_url: str | None
    city: str | None
    state: str | None
    country_code: str
    started_running_year: int | None
    favorite_distance: str | None
    onboarding_completed: bool


class PrivacyUpdate(BaseModel):
    profile_visibility: Visibility
    activities_visibility: Visibility
    races_visibility: Visibility
    medals_visibility: Visibility
    photos_visibility: Visibility
    locations_visibility: Visibility
    show_real_name: bool
    show_times: bool
    approve_followers: bool


class PrivacyResponse(PrivacyUpdate):
    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    profile: ProfileResponse
    privacy: PrivacyResponse
    providers: list[str]
    strava_connected: bool
