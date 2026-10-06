from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Activity, Location, Medal, Race, User


@dataclass(frozen=True)
class AchievementDefinition:
    code: str
    title: str
    description: str
    metric: str
    target: int
    category: str


ACHIEVEMENTS = [
    AchievementDefinition(
        "first_race", "Linha de largada", "Confirme sua primeira prova.", "races", 1, "provas"
    ),
    AchievementDefinition(
        "five_races", "Colecionador de largadas", "Complete 5 provas.", "races", 5, "provas"
    ),
    AchievementDefinition(
        "ten_races", "Calendário cheio", "Complete 10 provas.", "races", 10, "provas"
    ),
    AchievementDefinition(
        "first_5k", "Primeiros 5K", "Complete uma prova de 5 km.", "5K", 1, "distâncias"
    ),
    AchievementDefinition(
        "first_10k", "Primeiros 10K", "Complete uma prova de 10 km.", "10K", 1, "distâncias"
    ),
    AchievementDefinition(
        "first_half", "Meia conquistada", "Complete uma meia maratona.", "21K", 1, "distâncias"
    ),
    AchievementDefinition(
        "first_marathon", "Maratonista", "Complete uma maratona.", "42K", 1, "distâncias"
    ),
    AchievementDefinition(
        "first_ultra", "Além da maratona", "Complete uma ultramaratona.", "ULTRA", 1, "distâncias"
    ),
    AchievementDefinition(
        "five_medals", "Porta-medalhas", "Guarde 5 medalhas.", "medals", 5, "coleção"
    ),
    AchievementDefinition(
        "three_countries", "Passaporte corredor", "Corra em 3 países.", "countries", 3, "lugares"
    ),
    AchievementDefinition(
        "thousand_km",
        "Mil quilômetros",
        "Some 1.000 km de corrida.",
        "kilometers",
        1000,
        "consistência",
    ),
]


def personal_records(db: Session, user: User) -> list[dict[str, Any]]:
    races = db.scalars(
        select(Race).where(Race.user_id == user.id, Race.net_time_seconds.is_not(None))
    ).all()
    best: dict[str, Race] = {}
    for race in races:
        current = best.get(race.category)
        if not current or race.net_time_seconds < current.net_time_seconds:
            best[race.category] = race
    order = {"5K": 1, "10K": 2, "15K": 3, "21K": 4, "42K": 5, "ULTRA": 6, "OTHER": 7}
    records = []
    for race in sorted(best.values(), key=lambda item: order.get(item.category, 99)):
        kilometers = race.official_distance_meters / 1000
        records.append(
            {
                "race_id": race.id,
                "category": race.category,
                "event_name": race.event_name,
                "race_date": race.race_date,
                "time_seconds": race.net_time_seconds,
                "pace_seconds_per_km": round(race.net_time_seconds / kilometers),
                "city": race.city,
                "country_code": race.country_code,
            }
        )
    return records


def achievements(db: Session, user: User) -> list[dict[str, Any]]:
    race_counts = dict(
        db.execute(
            select(Race.category, func.count(Race.id))
            .where(Race.user_id == user.id)
            .group_by(Race.category)
        ).all()
    )
    total_races = sum(race_counts.values())
    medal_count = (
        db.scalar(select(func.count()).select_from(Medal).where(Medal.user_id == user.id)) or 0
    )
    distance = db.scalar(
        select(func.coalesce(func.sum(Activity.distance_meters), 0)).where(
            Activity.user_id == user.id
        )
    )
    training_countries = set(
        db.scalars(
            select(Location.country_code)
            .join(Activity)
            .where(Activity.user_id == user.id)
            .distinct()
        )
    )
    race_countries = set(db.scalars(select(Race.country_code).where(Race.user_id == user.id)))
    metrics = {
        "races": total_races,
        "medals": medal_count,
        "countries": len(training_countries | race_countries),
        "kilometers": int(float(distance) / 1000),
        **race_counts,
    }
    return [
        {
            "code": item.code,
            "title": item.title,
            "description": item.description,
            "unlocked": metrics.get(item.metric, 0) >= item.target,
            "progress": min(metrics.get(item.metric, 0), item.target),
            "target": item.target,
            "category": item.category,
        }
        for item in ACHIEVEMENTS
    ]
