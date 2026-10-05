from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Activity, StravaConnection, User
from app.services.tokens import decrypt_token, encrypt_token

settings = get_settings()
RUNNING_SPORTS = {"Run", "TrailRun", "VirtualRun", "Wheelchair"}


async def refresh_access_token(db: Session, connection: StravaConnection) -> str:
    if connection.expires_at > datetime.now(UTC) + timedelta(minutes=2):
        return decrypt_token(connection.access_token_encrypted)

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": decrypt_token(connection.refresh_token_encrypted),
            },
        )
    response.raise_for_status()
    token = response.json()
    connection.access_token_encrypted = encrypt_token(token["access_token"])
    connection.refresh_token_encrypted = encrypt_token(token["refresh_token"])
    connection.expires_at = datetime.fromtimestamp(token["expires_at"], tz=UTC)
    db.commit()
    return token["access_token"]


def _activity_values(payload: dict[str, Any]) -> dict[str, Any]:
    coordinates = payload.get("start_latlng") or [None, None]
    return {
        "name": payload.get("name") or "Corrida sem título",
        "sport_type": payload.get("sport_type") or payload.get("type") or "Run",
        "distance_meters": float(payload.get("distance") or 0),
        "moving_time_seconds": int(payload.get("moving_time") or 0),
        "elapsed_time_seconds": int(payload.get("elapsed_time") or 0),
        "elevation_gain": float(payload.get("total_elevation_gain") or 0),
        "started_at": datetime.fromisoformat(payload["start_date"].replace("Z", "+00:00")),
        "timezone": payload.get("timezone"),
        "start_latitude": coordinates[0],
        "start_longitude": coordinates[1],
        "summary_polyline": (payload.get("map") or {}).get("summary_polyline"),
        "is_commute": bool(payload.get("commute")),
        "is_manual": bool(payload.get("manual")),
        "source_visibility": payload.get("visibility") or "private",
        "raw_payload": payload,
    }


async def sync_strava_activities(db: Session, user: User, full: bool = False) -> dict[str, int]:
    connection = db.get(StravaConnection, user.id)
    if not connection:
        raise ValueError("Conecte sua conta Strava antes de sincronizar")

    connection.sync_status = "running"
    connection.sync_error = None
    db.commit()
    imported = 0
    updated = 0
    ignored = 0

    try:
        access_token = await refresh_access_token(db, connection)
        params: dict[str, int] = {"per_page": 100}
        if connection.last_synced_at and not full:
            params["after"] = int((connection.last_synced_at - timedelta(days=1)).timestamp())

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(1, settings.strava_sync_max_pages + 1):
                params["page"] = page
                response = await client.get(
                    "https://www.strava.com/api/v3/athlete/activities",
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                payloads = response.json()
                if not payloads:
                    break

                running = [
                    payload
                    for payload in payloads
                    if (payload.get("sport_type") or payload.get("type")) in RUNNING_SPORTS
                ]
                ignored += len(payloads) - len(running)
                external_ids = [str(payload["id"]) for payload in running]
                existing = {
                    activity.external_id: activity
                    for activity in db.scalars(
                        select(Activity).where(
                            Activity.user_id == user.id,
                            Activity.source == "strava",
                            Activity.external_id.in_(external_ids),
                        )
                    )
                }
                for payload in running:
                    external_id = str(payload["id"])
                    values = _activity_values(payload)
                    activity = existing.get(external_id)
                    if activity:
                        for field, value in values.items():
                            setattr(activity, field, value)
                        updated += 1
                    else:
                        db.add(
                            Activity(
                                user_id=user.id,
                                source="strava",
                                external_id=external_id,
                                local_visibility="private",
                                **values,
                            )
                        )
                        imported += 1
                db.commit()
                if len(payloads) < 100:
                    break

        connection.sync_status = "success"
        connection.sync_error = None
        connection.last_synced_at = datetime.now(UTC)
        connection.imported_activities = db.scalar(
            select(func.count()).select_from(Activity).where(Activity.user_id == user.id)
        )
        db.commit()
        return {"imported": imported, "updated": updated, "ignored": ignored}
    except Exception as exc:
        db.rollback()
        connection = db.get(StravaConnection, user.id)
        connection.sync_status = "failed"
        connection.sync_error = str(exc)[:500]
        db.commit()
        raise
