import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

RaceCategory = Literal["5K", "10K", "15K", "21K", "42K", "ULTRA", "OTHER"]
Visibility = Literal["public", "followers", "private"]


class RaceSuggestionResponse(BaseModel):
    id: uuid.UUID
    name: str
    started_at: datetime
    distance_meters: float
    moving_time_seconds: int
    workout_type: int | None
    suggested_category: str | None
    confidence: str
    score: int
    reasons: list[str]


class RaceCreate(BaseModel):
    activity_id: uuid.UUID | None = None
    event_name: str = Field(min_length=2, max_length=300)
    race_date: date
    category: RaceCategory
    official_distance_meters: float = Field(gt=0, le=1_000_000)
    recorded_distance_meters: float | None = Field(default=None, ge=0)
    net_time_seconds: int | None = Field(default=None, gt=0)
    gross_time_seconds: int | None = Field(default=None, gt=0)
    bib_number: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    result_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=3000)
    visibility: Visibility = "private"


class RaceConfirm(BaseModel):
    event_name: str | None = Field(default=None, min_length=2, max_length=300)
    category: RaceCategory | None = None
    official_distance_meters: float | None = Field(default=None, gt=0, le=1_000_000)
    net_time_seconds: int | None = Field(default=None, gt=0)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    visibility: Visibility = "private"


class RaceUpdate(BaseModel):
    event_name: str | None = Field(default=None, min_length=2, max_length=300)
    race_date: date | None = None
    category: RaceCategory | None = None
    official_distance_meters: float | None = Field(default=None, gt=0, le=1_000_000)
    net_time_seconds: int | None = Field(default=None, gt=0)
    gross_time_seconds: int | None = Field(default=None, gt=0)
    bib_number: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    result_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=3000)
    visibility: Visibility | None = None


class RaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_id: uuid.UUID | None
    event_name: str
    race_date: date
    category: str
    official_distance_meters: float
    recorded_distance_meters: float | None
    net_time_seconds: int | None
    gross_time_seconds: int | None
    bib_number: str | None
    city: str | None
    state: str | None
    country_code: str
    result_url: str | None
    notes: str | None
    visibility: str


class RaceListResponse(BaseModel):
    items: list[RaceResponse]
    total: int
