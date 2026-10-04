import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.models import User, UserSession
from app.services.oauth import (
    find_or_create_google_user,
    find_or_create_strava_user,
    oauth,
    provider_configured,
)
from app.services.sessions import (
    clear_session_cookie,
    create_session,
    get_current_user,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def ensure_provider(provider: str) -> None:
    if not provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Login com {provider.title()} ainda não foi configurado neste ambiente",
        )


@router.get("/google/login")
async def google_login(request: Request) -> Response:
    ensure_provider("google")
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)) -> Response:
    ensure_provider("google")
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email_verified"):
        raise HTTPException(status_code=400, detail="Conta Google sem e-mail verificado")
    user = find_or_create_google_user(db, user_info)
    response = RedirectResponse(f"{settings.frontend_url}/onboarding")
    set_session_cookie(response, create_session(db, user))
    return response


@router.get("/strava/login")
async def strava_login(request: Request) -> Response:
    ensure_provider("strava")
    redirect_uri = request.url_for("strava_callback")
    return await oauth.strava.authorize_redirect(
        request, redirect_uri, approval_prompt="auto", scope="read,activity:read"
    )


@router.get("/strava/callback", name="strava_callback")
async def strava_callback(request: Request, db: Session = Depends(get_db)) -> Response:
    ensure_provider("strava")
    token = await oauth.strava.authorize_access_token(request)
    if "athlete" not in token:
        raise HTTPException(status_code=400, detail="O Strava não retornou os dados do atleta")
    user = find_or_create_strava_user(db, token)
    response = RedirectResponse(f"{settings.frontend_url}/onboarding")
    set_session_cookie(response, create_session(db, user))
    return response


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))
        db.commit()
    clear_session_cookie(response)
