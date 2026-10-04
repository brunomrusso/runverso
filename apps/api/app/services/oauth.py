from datetime import UTC, datetime
from typing import Any

from authlib.integrations.starlette_client import OAuth
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AuthIdentity, PrivacySettings, Profile, StravaConnection, User
from app.services.tokens import encrypt_token

settings = get_settings()
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
oauth.register(
    name="strava",
    client_id=settings.strava_client_id,
    client_secret=settings.strava_client_secret,
    authorize_url="https://www.strava.com/oauth/authorize",
    access_token_url="https://www.strava.com/oauth/token",
    client_kwargs={"scope": "read,activity:read"},
)


def provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(settings.google_client_id and settings.google_client_secret)
    return bool(settings.strava_client_id and settings.strava_client_secret)


def find_or_create_google_user(db: Session, user_info: dict[str, Any]) -> User:
    provider_user_id = str(user_info["sub"])
    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.provider == "google",
            AuthIdentity.provider_user_id == provider_user_id,
        )
    )
    if identity:
        return identity.user

    email = user_info["email"].lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()
        db.add(
            Profile(
                user_id=user.id,
                real_name=user_info.get("name"),
                display_name=user_info.get("given_name") or user_info.get("name"),
                avatar_url=user_info.get("picture"),
            )
        )
        db.add(PrivacySettings(user_id=user.id))
    db.add(AuthIdentity(user_id=user.id, provider="google", provider_user_id=provider_user_id))
    db.commit()
    db.refresh(user)
    return user


def find_or_create_strava_user(db: Session, token: dict[str, Any]) -> User:
    athlete = token["athlete"]
    athlete_id = str(athlete["id"])
    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.provider == "strava",
            AuthIdentity.provider_user_id == athlete_id,
        )
    )
    if identity:
        user = identity.user
    else:
        user = User(email=f"strava-{athlete_id}@users.runverso.local")
        db.add(user)
        db.flush()
        full_name = " ".join(filter(None, [athlete.get("firstname"), athlete.get("lastname")]))
        db.add(
            Profile(
                user_id=user.id,
                real_name=full_name or None,
                display_name=athlete.get("firstname") or full_name or "Corredor",
                avatar_url=athlete.get("profile"),
                city=athlete.get("city"),
                state=athlete.get("state"),
                country_code="BR",
            )
        )
        db.add(PrivacySettings(user_id=user.id))
        db.add(AuthIdentity(user_id=user.id, provider="strava", provider_user_id=athlete_id))

    expires_at = datetime.fromtimestamp(token["expires_at"], tz=UTC)
    connection = db.get(StravaConnection, user.id)
    values = {
        "athlete_id": athlete_id,
        "access_token_encrypted": encrypt_token(token["access_token"]),
        "refresh_token_encrypted": encrypt_token(token["refresh_token"]),
        "expires_at": expires_at,
        "scopes": "read,activity:read",
    }
    if connection:
        for key, value in values.items():
            setattr(connection, key, value)
    else:
        db.add(StravaConnection(user_id=user.id, **values))
    db.commit()
    db.refresh(user)
    return user
