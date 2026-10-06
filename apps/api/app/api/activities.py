import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models import Activity, User
from app.schemas.activity import (
    ActivityListResponse,
    ActivityResponse,
    ActivityStatsResponse,
    ActivityTrendsResponse,
    DistancePointResponse,
    SyncResponse,
    SyncStatusResponse,
)
from app.services.sessions import get_current_user
from app.services.strava import sync_strava_activities

router = APIRouter(tags=["activities"])


@router.post("/strava/sync", response_model=SyncResponse)
async def sync_strava(
    full: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    try:
        return await sync_strava_activities(db, user, full=full)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"O Strava recusou a sincronização ({exc.response.status_code})",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Não foi possível acessar o Strava") from exc


@router.get("/strava/sync/status", response_model=SyncStatusResponse)
def sync_status(user: User = Depends(get_current_user)) -> SyncStatusResponse:
    connection = user.strava_connection
    if not connection:
        return SyncStatusResponse(
            connected=False,
            status=None,
            error=None,
            imported_activities=0,
            last_synced_at=None,
        )
    return SyncStatusResponse(
        connected=True,
        status=connection.sync_status,
        error=connection.sync_error,
        imported_activities=connection.imported_activities,
        last_synced_at=connection.last_synced_at,
    )


@router.get("/activities", response_model=ActivityListResponse)
def list_activities(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityListResponse:
    filters = [Activity.user_id == user.id]
    total = db.scalar(select(func.count()).select_from(Activity).where(*filters)) or 0
    activities = db.scalars(
        select(Activity)
        .where(*filters)
        .order_by(desc(Activity.started_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    return ActivityListResponse(
        items=[ActivityResponse.model_validate(activity) for activity in activities],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/activities/stats", response_model=ActivityStatsResponse)
def activity_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityStatsResponse:
    row = db.execute(
        select(
            func.count(Activity.id),
            func.coalesce(func.sum(Activity.distance_meters), 0),
            func.coalesce(func.sum(Activity.moving_time_seconds), 0),
            func.max(Activity.started_at),
        ).where(Activity.user_id == user.id)
    ).one()
    return ActivityStatsResponse(
        total=row[0],
        total_distance_meters=float(row[1]),
        total_moving_time_seconds=row[2],
        latest_activity_at=row[3],
    )


def distance_points(
    db: Session, user: User, bucket: str, count: int
) -> list[DistancePointResponse]:
    period = func.date_trunc(bucket, Activity.started_at)
    rows = db.execute(
        select(
            period,
            func.count(Activity.id),
            func.coalesce(func.sum(Activity.distance_meters), 0),
        )
        .where(Activity.user_id == user.id)
        .group_by(period)
        .order_by(desc(period))
        .limit(count)
    ).all()
    points = [
        DistancePointResponse(
            label=row[0].date().isoformat(),
            count=row[1],
            distance_km=round(float(row[2]) / 1000, 1),
        )
        for row in rows
    ]
    return list(reversed(points))


@router.get("/activities/trends", response_model=ActivityTrendsResponse)
def activity_trends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityTrendsResponse:
    return ActivityTrendsResponse(
        weekly=distance_points(db, user, "week", 12),
        monthly=distance_points(db, user, "month", 12),
    )
