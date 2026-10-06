from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dependencies.database import get_db
from app.models import User
from app.schemas.social import (
    FeedResponse,
    FollowersResponse,
    FollowResponse,
    PublicProfileResponse,
    RunnerSearchResponse,
)
from app.services.sessions import find_session, get_current_user
from app.services.social import (
    answer_follow_request,
    community_feed,
    follow_runner,
    follower_overview,
    public_overview,
    search_runners,
    unfollow_runner,
)

router = APIRouter(tags=["social"])
settings = get_settings()


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    session = find_session(db, request.cookies.get(settings.session_cookie_name))
    return session.user if session else None


@router.get("/feed", response_model=FeedResponse)
def feed(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> FeedResponse:
    return FeedResponse(items=community_feed(db, user))


@router.get("/community/runners", response_model=RunnerSearchResponse)
def runners(
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunnerSearchResponse:
    if len(q.strip()) < 2:
        return RunnerSearchResponse(items=[])
    return RunnerSearchResponse(items=search_runners(db, user, q))


@router.get("/me/followers", response_model=FollowersResponse)
def my_followers(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    return follower_overview(db, user)


@router.post("/me/followers/{username}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_follower(
    username: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        answer_follow_request(db, user, username, accept=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/followers/{username}", status_code=status.HTTP_204_NO_CONTENT)
def reject_or_remove_follower(
    username: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        answer_follow_request(db, user, username, accept=False)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/community/{username}", response_model=PublicProfileResponse)
def community_profile(
    username: str,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(optional_user),
) -> dict:
    overview = public_overview(db, username, viewer)
    if not overview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return overview


@router.post("/users/{username}/follow", response_model=FollowResponse)
def follow(
    username: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FollowResponse:
    try:
        follow_status, followers = follow_runner(db, user, username)
    except ValueError as exc:
        not_found = str(exc) == "not_found"
        detail = "Perfil não encontrado" if not_found else "Você não pode seguir a si mesmo"
        raise HTTPException(status_code=404 if not_found else 400, detail=detail) from exc
    return FollowResponse(status=follow_status, follower_count=followers)


@router.delete("/users/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(
    username: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        unfollow_runner(db, user, username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Perfil não encontrado") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
