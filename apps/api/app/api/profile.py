import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.models import Follow, PrivacySettings, Profile, User
from app.schemas.profile import (
    CurrentUserResponse,
    PrivacyResponse,
    PrivacyUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.images import resolve_upload, save_avatar
from app.services.sessions import find_session, get_current_user

router = APIRouter(tags=["profile"])
settings = get_settings()


def serialize_user(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=str(user.id),
        email=user.email,
        profile=ProfileResponse.model_validate(user.profile),
        privacy=PrivacyResponse.model_validate(user.privacy_settings),
        providers=sorted(identity.provider for identity in user.identities),
        strava_connected=user.strava_connection is not None,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return serialize_user(user)


@router.patch("/me/profile", response_model=CurrentUserResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    for field, value in payload.model_dump().items():
        setattr(user.profile, field, value)
    user.profile.onboarding_completed = True
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este nome de usuário já está em uso") from exc
    db.refresh(user.profile)
    return serialize_user(user)


@router.post("/me/avatar", response_model=CurrentUserResponse)
async def upload_avatar(
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    await save_avatar(photo, user.id)
    user.profile.avatar_url = f"/avatars/{user.id}?v={int(datetime.now().timestamp())}"
    db.commit()
    db.refresh(user.profile)
    return serialize_user(user)


@router.get("/avatars/{user_id}")
def avatar(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> FileResponse:
    runner = db.get(User, user_id)
    if not runner or not runner.profile or not runner.privacy_settings:
        raise HTTPException(status_code=404, detail="Avatar não encontrado")
    session = find_session(db, request.cookies.get(settings.session_cookie_name))
    viewer = session.user if session else None
    privacy = runner.privacy_settings.profile_visibility
    allowed = privacy == "public" or (viewer and viewer.id == runner.id)
    if privacy == "followers" and viewer:
        allowed = db.scalar(
            select(Follow.id).where(
                Follow.follower_id == viewer.id,
                Follow.following_id == runner.id,
                Follow.status == "accepted",
            )
        ) is not None
    if not allowed:
        raise HTTPException(status_code=404, detail="Avatar não encontrado")
    path = resolve_upload(f"{runner.id}/avatar/avatar.jpg")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Avatar não encontrado")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/me/privacy", response_model=PrivacyResponse)
def get_privacy(user: User = Depends(get_current_user)) -> PrivacySettings:
    return user.privacy_settings


@router.patch("/me/privacy", response_model=PrivacyResponse)
def update_privacy(
    payload: PrivacyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PrivacySettings:
    for field, value in payload.model_dump().items():
        setattr(user.privacy_settings, field, value)
    db.commit()
    db.refresh(user.privacy_settings)
    return user.privacy_settings


@router.get("/users/{username}", response_model=ProfileResponse)
def public_profile(username: str, db: Session = Depends(get_db)) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.username == username.lower()))
    if not profile or profile.user.privacy_settings.profile_visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    response = ProfileResponse.model_validate(profile)
    if not profile.user.privacy_settings.show_real_name:
        response.real_name = None
    return response
