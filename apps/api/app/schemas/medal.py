import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Visibility = Literal["public", "followers", "private"]
PhotoKind = Literal["front", "back", "gallery"]


class MedalCreate(BaseModel):
    race_id: uuid.UUID
    title: str | None = Field(default=None, max_length=200)
    story: str | None = Field(default=None, max_length=3000)
    is_favorite: bool = False
    visibility: Visibility = "private"


class MedalUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    story: str | None = Field(default=None, max_length=3000)
    is_favorite: bool | None = None
    visibility: Visibility | None = None


class MedalPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    content_type: str
    sort_order: int
    image_url: str
    thumbnail_url: str


class MedalRaceResponse(BaseModel):
    id: uuid.UUID
    event_name: str
    race_date: str
    category: str
    city: str | None
    state: str | None


class MedalResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    story: str | None
    is_favorite: bool
    visibility: str
    race: MedalRaceResponse
    photos: list[MedalPhotoResponse]


class MedalListResponse(BaseModel):
    items: list[MedalResponse]
    total: int
