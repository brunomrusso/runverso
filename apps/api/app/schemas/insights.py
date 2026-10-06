import uuid
from datetime import date

from pydantic import BaseModel


class PersonalRecordResponse(BaseModel):
    race_id: uuid.UUID
    category: str
    event_name: str
    race_date: date
    time_seconds: int
    pace_seconds_per_km: int
    city: str | None
    country_code: str


class AchievementResponse(BaseModel):
    code: str
    title: str
    description: str
    unlocked: bool
    progress: int
    target: int
    category: str


class InsightsResponse(BaseModel):
    records: list[PersonalRecordResponse]
    achievements: list[AchievementResponse]
    unlocked_count: int
    total_count: int
