import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models import Activity, Race, User
from app.schemas.race import (
    RaceConfirm,
    RaceCreate,
    RaceListResponse,
    RaceResponse,
    RaceSuggestionResponse,
    RaceUpdate,
)
from app.services.races import classify_activity, official_distance
from app.services.sessions import get_current_user

router = APIRouter(tags=["races"])


def owned_activity(db: Session, user: User, activity_id: uuid.UUID) -> Activity:
    activity = db.scalar(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == user.id)
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    return activity


def owned_race(db: Session, user: User, race_id: uuid.UUID) -> Race:
    race = db.scalar(select(Race).where(Race.id == race_id, Race.user_id == user.id))
    if not race:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    return race


@router.get("/race-suggestions", response_model=list[RaceSuggestionResponse])
def race_suggestions(
    confidence: str | None = Query(default=None, pattern="^(high|medium|low)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RaceSuggestionResponse]:
    activities = db.scalars(
        select(Activity).where(
            Activity.user_id == user.id,
            Activity.race_candidate_status.notin_(["confirmed", "rejected"]),
        )
    ).all()
    for activity in activities:
        classify_activity(activity)
    db.commit()

    suggested = [item for item in activities if item.race_candidate_status == "suggested"]
    if confidence:
        suggested = [item for item in suggested if item.suggestion_confidence == confidence]
    suggested.sort(key=lambda item: (item.suggestion_score, item.started_at), reverse=True)
    return [
        RaceSuggestionResponse(
            id=item.id,
            name=item.name,
            started_at=item.started_at,
            distance_meters=item.distance_meters,
            moving_time_seconds=item.moving_time_seconds,
            workout_type=item.workout_type,
            suggested_category=item.suggested_category,
            confidence=item.suggestion_confidence or "low",
            score=item.suggestion_score,
            reasons=item.suggestion_reasons,
        )
        for item in suggested
    ]


@router.post("/race-suggestions/{activity_id}/confirm", response_model=RaceResponse)
def confirm_suggestion(
    activity_id: uuid.UUID,
    payload: RaceConfirm,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Race:
    activity = owned_activity(db, user, activity_id)
    if activity.race:
        raise HTTPException(status_code=409, detail="Esta atividade já está vinculada a uma prova")
    category = payload.category or activity.suggested_category or "OTHER"
    race = Race(
        user_id=user.id,
        activity_id=activity.id,
        event_name=payload.event_name or activity.name,
        race_date=activity.started_at.date(),
        category=category,
        official_distance_meters=payload.official_distance_meters
        or official_distance(category, activity.distance_meters),
        recorded_distance_meters=activity.distance_meters,
        net_time_seconds=payload.net_time_seconds or activity.moving_time_seconds,
        gross_time_seconds=activity.elapsed_time_seconds,
        city=payload.city,
        state=payload.state,
        country_code=payload.country_code.upper(),
        visibility=payload.visibility,
    )
    activity.race_candidate_status = "confirmed"
    db.add(race)
    db.commit()
    db.refresh(race)
    return race


@router.post("/race-suggestions/{activity_id}/reject", status_code=204)
def reject_suggestion(
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    activity = owned_activity(db, user, activity_id)
    activity.race_candidate_status = "rejected"
    db.commit()


@router.post("/races", response_model=RaceResponse, status_code=status.HTTP_201_CREATED)
def create_race(
    payload: RaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Race:
    values = payload.model_dump()
    values["country_code"] = payload.country_code.upper()
    values["result_url"] = str(payload.result_url) if payload.result_url else None
    activity = None
    if payload.activity_id:
        activity = owned_activity(db, user, payload.activity_id)
        if activity.race:
            raise HTTPException(status_code=409, detail="Atividade já vinculada a uma prova")
        activity.race_candidate_status = "confirmed"
    race = Race(user_id=user.id, **values)
    db.add(race)
    db.commit()
    db.refresh(race)
    return race


@router.get("/races", response_model=RaceListResponse)
def list_races(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RaceListResponse:
    races = db.scalars(
        select(Race).where(Race.user_id == user.id).order_by(desc(Race.race_date))
    ).all()
    return RaceListResponse(
        items=[RaceResponse.model_validate(item) for item in races], total=len(races)
    )


@router.get("/races/count")
def race_count(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, int]:
    total = db.scalar(select(func.count()).select_from(Race).where(Race.user_id == user.id)) or 0
    return {"total": total}


@router.patch("/races/{race_id}", response_model=RaceResponse)
def update_race(
    race_id: uuid.UUID,
    payload: RaceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Race:
    race = owned_race(db, user, race_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "result_url" and value is not None:
            value = str(value)
        if field == "country_code" and value is not None:
            value = value.upper()
        setattr(race, field, value)
    db.commit()
    db.refresh(race)
    return race


@router.delete("/races/{race_id}", status_code=204)
def delete_race(
    race_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    race = owned_race(db, user, race_id)
    if race.activity:
        race.activity.race_candidate_status = "pending"
    db.delete(race)
    db.commit()
