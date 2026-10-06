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


class RunnerSummaryResponse(BaseModel):
    username: str
    display_name: str | None
    avatar_url: str | None
    city: str | None
    state: str | None
    country_code: str
    follower_count: int
    viewer_follow_status: str | None


class RunnerSearchResponse(BaseModel):
    items: list[RunnerSummaryResponse]


class FollowersResponse(BaseModel):
    followers: list[RunnerSummaryResponse]
    pending: list[RunnerSummaryResponse]
    following: list[RunnerSummaryResponse]


class FeedItemResponse(BaseModel):
    id: str
    target_type: str
    target_id: str
    kind: str
    username: str
    display_name: str | None
    title: str
    subtitle: str | None
    happened_at: str
    like_count: int
    viewer_liked: bool


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]


class ReactionResponse(BaseModel):
    liked: bool
    like_count: int


class NotificationResponse(BaseModel):
    id: str
    kind: str
    message: str
    actor_username: str | None
    actor_display_name: str | None
    is_read: bool
    created_at: str


class NotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
