from typing import Literal

from pydantic import BaseModel


class GeoPointResponse(BaseModel):
    country_code: str
    state: str | None
    city: str | None
    latitude: float
    longitude: float
    count: int


class CountryResponse(BaseModel):
    country_code: str
    country: str
    count: int
    distance_meters: float
    states: list[str]
    cities: list[str]
    state_count: int
    city_count: int


class GeographyResponse(BaseModel):
    mode: Literal["training", "races"]
    country_count: int
    state_count: int
    city_count: int
    countries: list[CountryResponse]
    points: list[GeoPointResponse]
