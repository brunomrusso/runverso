from pydantic import BaseModel, ConfigDict

from app.schemas.insights import PersonalRecordResponse
from app.schemas.profile import ProfileResponse


class PublicMedalResponse(BaseModel):
    id: str
    title: str | None
    is_favorite: bool
    race_name: str
    race_category: str
    race_date: str


class PublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile: ProfileResponse
    race_count: int | None
    medal_count: int | None
    country_count: int | None
    records: list[PersonalRecordResponse] | None
    medals: list[PublicMedalResponse] | None
    follower_count: int
    following_count: int
    viewer_follow_status: str | None
    is_own_profile: bool


class FollowResponse(BaseModel):
    status: str
    follower_count: int
