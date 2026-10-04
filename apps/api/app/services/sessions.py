import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.models import User, UserSession

settings = get_settings()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(48)
    session = UserSession(
        user_id=user.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_days),
    )
    db.add(session)
    db.commit()
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.environment != "local",
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


def find_session(db: Session, token: str | None) -> UserSession | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.scalar(
        select(UserSession)
        .options(
            selectinload(UserSession.user).selectinload(User.profile),
            selectinload(UserSession.user).selectinload(User.privacy_settings),
            selectinload(UserSession.user).selectinload(User.identities),
            selectinload(UserSession.user).selectinload(User.strava_connection),
        )
        .where(UserSession.token_hash == token_hash)
    )
    if session and session.expires_at > datetime.now(UTC):
        return session
    if session:
        db.delete(session)
        db.commit()
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session = find_session(db, request.cookies.get(settings.session_cookie_name))
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    return session.user
