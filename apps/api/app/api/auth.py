import hashlib
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.models import AuthIdentity, StravaConnection, User, UserSession
from app.services.oauth import (
    find_or_create_google_user,
    find_or_create_strava_user,
    oauth,
    provider_configured,
)
from app.services.sessions import (
    clear_session_cookie,
    create_session,
    find_session,
    get_current_user,
    set_session_cookie,
)
from app.services.tokens import decrypt_token

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
    destination = "dashboard" if user.profile.onboarding_completed else "onboarding"
    response = RedirectResponse(f"{settings.frontend_url}/{destination}")
    set_session_cookie(response, create_session(db, user))
    return response


@router.get("/strava/login")
async def strava_login(request: Request) -> Response:
    ensure_provider("strava")
    request.session.pop("strava_link_user_id", None)
    redirect_uri = request.url_for("strava_callback")
    return await oauth.strava.authorize_redirect(
        request, redirect_uri, approval_prompt="auto", scope="read,activity:read"
    )


@router.get("/strava/link")
async def strava_link(request: Request, user: User = Depends(get_current_user)) -> Response:
    ensure_provider("strava")
    if user.strava_connection:
        return RedirectResponse(f"{settings.frontend_url}/dashboard")
    request.session["strava_link_user_id"] = str(user.id)
    redirect_uri = request.url_for("strava_callback")
    return await oauth.strava.authorize_redirect(
        request, redirect_uri, approval_prompt="force", scope="read,activity:read"
    )


@router.get("/strava/callback", name="strava_callback")
async def strava_callback(request: Request, db: Session = Depends(get_db)) -> Response:
    ensure_provider("strava")
    token = await oauth.strava.authorize_access_token(request)
    if "athlete" not in token and token.get("access_token"):
        async with httpx.AsyncClient(timeout=10) as client:
            athlete_response = await client.get(
                "https://www.strava.com/api/v3/athlete",
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
        if athlete_response.is_success:
            token["athlete"] = athlete_response.json()
    if "athlete" not in token:
        raise HTTPException(status_code=502, detail="Não foi possível consultar o atleta no Strava")
    link_user_id = request.session.pop("strava_link_user_id", None)
    target_user = db.get(User, uuid.UUID(link_user_id)) if link_user_id else None
    active_session = find_session(
        db, request.cookies.get(settings.session_cookie_name)
    ) if link_user_id else None
    if link_user_id and (
        not target_user or not active_session or active_session.user_id != target_user.id
    ):
        raise HTTPException(status_code=401, detail="A sessão de vinculação expirou")
    try:
        user = find_or_create_strava_user(db, token, target_user=target_user)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    destination = "dashboard" if user.profile.onboarding_completed else "onboarding"
    response = RedirectResponse(f"{settings.frontend_url}/{destination}")
    if not target_user:
        set_session_cookie(response, create_session(db, user))
    return response


@router.delete("/strava", status_code=204)
async def disconnect_strava(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    connection = db.get(StravaConnection, user.id)
    if not connection:
        return
    providers = {identity.provider for identity in user.identities}
    if providers == {"strava"}:
        raise HTTPException(
            status_code=409,
            detail="Vincule o Google antes de desconectar seu único método de acesso",
        )
    access_token = decrypt_token(connection.access_token_encrypted)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://www.strava.com/oauth/deauthorize",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="O Strava não confirmou a desconexão")
    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.user_id == user.id,
            AuthIdentity.provider == "strava",
        )
    )
    db.delete(connection)
    if identity:
        db.delete(identity)
    db.commit()


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
