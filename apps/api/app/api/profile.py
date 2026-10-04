from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models import PrivacySettings, Profile, User
from app.schemas.profile import (
    CurrentUserResponse,
    PrivacyResponse,
    PrivacyUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.sessions import get_current_user

router = APIRouter(tags=["profile"])


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
