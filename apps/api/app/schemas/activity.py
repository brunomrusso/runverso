import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    name: str
    sport_type: str
    distance_meters: float
    moving_time_seconds: int
    elapsed_time_seconds: int
    elevation_gain: float
    started_at: datetime
    source_visibility: str
    local_visibility: str


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    per_page: int


class ActivityStatsResponse(BaseModel):
    total: int
    total_distance_meters: float
    total_moving_time_seconds: int
    latest_activity_at: datetime | None


class SyncResponse(BaseModel):
    imported: int
    updated: int
    ignored: int


class SyncStatusResponse(BaseModel):
    connected: bool
    status: str | None
    error: str | None
    imported_activities: int
    last_synced_at: datetime | None
