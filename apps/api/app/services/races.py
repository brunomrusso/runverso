from dataclasses import dataclass

from app.models import Activity


@dataclass(frozen=True)
class DistanceCategory:
    name: str
    official_meters: float
    minimum: float
    maximum: float | None


CATEGORIES = [
    DistanceCategory("5K", 5000, 4700, 5400),
    DistanceCategory("10K", 10000, 9500, 10600),
    DistanceCategory("15K", 15000, 14300, 15800),
    DistanceCategory("21K", 21097.5, 20000, 22200),
    DistanceCategory("42K", 42195, 40000, 42500),
    DistanceCategory("ULTRA", 50000, 42500, None),
]
EVENT_KEYWORDS = {
    "prova",
    "race",
    "maratona",
    "meia maratona",
    "circuito",
    "etapa",
    "corrida de rua",
    "desafio",
    "challenge",
}


def distance_category(distance_meters: float) -> DistanceCategory | None:
    for category in CATEGORIES:
        if distance_meters >= category.minimum and (
            category.maximum is None or distance_meters <= category.maximum
        ):
            return category
    return None


def classify_activity(activity: Activity) -> None:
    if activity.race_candidate_status in {"confirmed", "rejected"}:
        return

    score = 0
    reasons: list[str] = []
    category = distance_category(activity.distance_meters)
    if activity.workout_type == 1:
        score += 70
        reasons.append("Marcada como prova no Strava")
    if category:
        score += 20
        reasons.append(
            f"Distância de {activity.distance_meters / 1000:.2f} km próxima de {category.name}"
        )
    normalized_name = activity.name.casefold()
    matched_keywords = [keyword for keyword in EVENT_KEYWORDS if keyword in normalized_name]
    if matched_keywords:
        score += 25
        reasons.append(f"Nome contém “{matched_keywords[0]}”")
    athlete_count = int(activity.raw_payload.get("athlete_count") or 0)
    if athlete_count > 1:
        score += 10
        reasons.append("Atividade realizada com outros atletas")

    activity.suggested_category = category.name if category else None
    activity.suggestion_score = score
    activity.suggestion_reasons = reasons
    activity.suggestion_confidence = "high" if score >= 70 else "medium" if score >= 45 else "low"
    activity.race_candidate_status = "suggested" if score >= 20 else "not_candidate"


def official_distance(category: str, fallback: float) -> float:
    match = next((item for item in CATEGORIES if item.name == category), None)
    return match.official_meters if match else fallback
