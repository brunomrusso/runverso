from typing import Any

import reverse_geocode
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session, selectinload

from app.models import Activity, Location, Race, User


def coordinate_bucket(latitude: float, longitude: float) -> tuple[float, float]:
    return round(latitude, 2), round(longitude, 2)


def process_activity_locations(db: Session, user: User) -> dict[str, int]:
    activities = db.scalars(
        select(Activity).where(
            Activity.user_id == user.id,
            Activity.location_id.is_(None),
            Activity.start_latitude.is_not(None),
            Activity.start_longitude.is_not(None),
        )
    ).all()
    if not activities:
        return {"processed": 0, "without_coordinates": 0}

    buckets = {
        coordinate_bucket(activity.start_latitude, activity.start_longitude)
        for activity in activities
    }
    existing = {
        (location.latitude_bucket, location.longitude_bucket): location
        for location in db.scalars(
            select(Location).where(
                tuple_(Location.latitude_bucket, Location.longitude_bucket).in_(list(buckets))
            )
        )
    }
    missing = sorted(buckets - set(existing))
    if missing:
        results = reverse_geocode.search(missing)
        for bucket, result in zip(missing, results, strict=True):
            location = Location(
                latitude_bucket=bucket[0],
                longitude_bucket=bucket[1],
                city=result.get("city"),
                state=result.get("state"),
                country=result.get("country") or result.get("country_code") or "Desconhecido",
                country_code=(result.get("country_code") or "XX").upper(),
                display_latitude=float(result.get("latitude") or bucket[0]),
                display_longitude=float(result.get("longitude") or bucket[1]),
            )
            db.add(location)
            db.flush()
            existing[bucket] = location

    for activity in activities:
        bucket = coordinate_bucket(activity.start_latitude, activity.start_longitude)
        activity.location_id = existing[bucket].id
    db.commit()
    return {"processed": len(activities), "without_coordinates": 0}


def geography_summary(db: Session, user: User, mode: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if mode == "training":
        activities = db.scalars(
            select(Activity)
            .options(selectinload(Activity.location))
            .where(Activity.user_id == user.id, Activity.location_id.is_not(None))
        ).all()
        records = [
            {
                "country_code": item.location.country_code,
                "country": item.location.country,
                "state": item.location.state,
                "city": item.location.city,
                "latitude": item.location.display_latitude,
                "longitude": item.location.display_longitude,
                "distance": item.distance_meters,
            }
            for item in activities
        ]
    else:
        races = db.scalars(
            select(Race)
            .options(selectinload(Race.activity).selectinload(Activity.location))
            .where(Race.user_id == user.id)
        ).all()
        for race in races:
            location = race.activity.location if race.activity else None
            records.append(
                {
                    "country_code": race.country_code,
                    "country": location.country if location else race.country_code,
                    "state": race.state or (location.state if location else None),
                    "city": race.city or (location.city if location else None),
                    "latitude": location.display_latitude if location else None,
                    "longitude": location.display_longitude if location else None,
                    "distance": race.official_distance_meters,
                }
            )

    countries: dict[str, dict[str, Any]] = {}
    points: dict[tuple[str, str | None, str | None], dict[str, Any]] = {}
    for record in records:
        code = record["country_code"] or "XX"
        country = countries.setdefault(
            code,
            {
                "country_code": code,
                "country": record["country"],
                "count": 0,
                "distance_meters": 0.0,
                "states": set(),
                "cities": set(),
            },
        )
        country["count"] += 1
        country["distance_meters"] += record["distance"]
        if record["state"]:
            country["states"].add(record["state"])
        if record["city"]:
            country["cities"].add(record["city"])
        key = (code, record["state"], record["city"])
        point = points.setdefault(
            key,
            {
                "country_code": code,
                "state": record["state"],
                "city": record["city"],
                "latitude": record["latitude"],
                "longitude": record["longitude"],
                "count": 0,
            },
        )
        point["count"] += 1

    country_list = []
    for item in countries.values():
        country_list.append(
            {
                **item,
                "states": sorted(item["states"]),
                "cities": sorted(item["cities"]),
                "state_count": len(item["states"]),
                "city_count": len(item["cities"]),
            }
        )
    country_list.sort(key=lambda item: item["count"], reverse=True)
    return {
        "mode": mode,
        "country_count": len(country_list),
        "state_count": len({state for item in country_list for state in item["states"]}),
        "city_count": len({city for item in country_list for city in item["cities"]}),
        "countries": country_list,
        "points": [point for point in points.values() if point["latitude"] is not None],
    }
