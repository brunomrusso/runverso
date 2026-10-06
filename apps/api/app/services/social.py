from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Follow, Medal, PrivacySettings, Profile, Race, User
from app.schemas.profile import ProfileResponse
from app.services.insights import personal_records


def profile_user(db: Session, username: str) -> User | None:
    return db.scalar(select(User).join(Profile).where(Profile.username == username.lower()))


def follow_state(db: Session, follower: User | None, following: User) -> Follow | None:
    if not follower:
        return None
    return db.scalar(
        select(Follow).where(
            Follow.follower_id == follower.id, Follow.following_id == following.id
        )
    )


def accepted_follower_count(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Follow)
        .where(Follow.following_id == user.id, Follow.status == "accepted")
    ) or 0


def accepted_following_count(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Follow)
        .where(Follow.follower_id == user.id, Follow.status == "accepted")
    ) or 0


def can_view(owner: User, viewer: User | None, visibility: str, follow: Follow | None) -> bool:
    if visibility == "public" or (viewer and viewer.id == owner.id):
        return True
    return visibility == "followers" and follow is not None and follow.status == "accepted"


def public_overview(db: Session, username: str, viewer: User | None) -> dict | None:
    runner = profile_user(db, username)
    if not runner:
        return None
    follow = follow_state(db, viewer, runner)
    privacy = runner.privacy_settings
    if not can_view(runner, viewer, privacy.profile_visibility, follow):
        return None
    races_visible = can_view(runner, viewer, privacy.races_visibility, follow)
    medals_visible = can_view(runner, viewer, privacy.medals_visibility, follow)
    locations_visible = can_view(runner, viewer, privacy.locations_visibility, follow)

    race_count = None
    records = None
    if races_visible:
        race_count = db.scalar(
            select(func.count()).select_from(Race).where(Race.user_id == runner.id)
        )
        records = personal_records(db, runner) if privacy.show_times else None

    medal_count = None
    medals = None
    if medals_visible:
        medal_items = db.scalars(
            select(Medal)
            .where(Medal.user_id == runner.id, Medal.visibility == "public")
            .order_by(Medal.created_at.desc())
            .limit(8)
        ).all()
        medal_count = db.scalar(
            select(func.count())
            .select_from(Medal)
            .where(Medal.user_id == runner.id, Medal.visibility == "public")
        )
        medals = [
            {
                "id": str(medal.id),
                "title": medal.title,
                "is_favorite": medal.is_favorite,
                "race_name": medal.race.event_name,
                "race_category": medal.race.category,
                "race_date": medal.race.race_date.isoformat(),
            }
            for medal in medal_items
        ]

    country_count = None
    if locations_visible:
        countries = {
            country
            for country in db.scalars(
                select(Race.country_code).where(Race.user_id == runner.id).distinct()
            )
            if country
        }
        country_count = len(countries)

    profile = ProfileResponse.model_validate(runner.profile)
    if not privacy.show_real_name:
        profile.real_name = None
    return {
        "profile": profile,
        "race_count": race_count,
        "medal_count": medal_count,
        "country_count": country_count,
        "records": records,
        "medals": medals,
        "follower_count": accepted_follower_count(db, runner),
        "following_count": accepted_following_count(db, runner),
        "viewer_follow_status": follow.status if follow else None,
        "is_own_profile": bool(viewer and viewer.id == runner.id),
    }


def follow_runner(db: Session, viewer: User, username: str) -> tuple[str, int]:
    runner = profile_user(db, username)
    if not runner or runner.privacy_settings.profile_visibility != "public":
        raise ValueError("not_found")
    if runner.id == viewer.id:
        raise ValueError("self_follow")
    status = "pending" if runner.privacy_settings.approve_followers else "accepted"
    existing = follow_state(db, viewer, runner)
    if existing:
        existing.status = status
    else:
        db.add(Follow(follower_id=viewer.id, following_id=runner.id, status=status))
    db.commit()
    return status, accepted_follower_count(db, runner)


def unfollow_runner(db: Session, viewer: User, username: str) -> int:
    runner = profile_user(db, username)
    if not runner:
        raise ValueError("not_found")
    follow = follow_state(db, viewer, runner)
    if follow:
        db.delete(follow)
        db.commit()
    return accepted_follower_count(db, runner)


def runner_summary(db: Session, runner: User, viewer: User) -> dict:
    follow = follow_state(db, viewer, runner)
    return {
        "username": runner.profile.username,
        "display_name": runner.profile.display_name,
        "city": runner.profile.city,
        "state": runner.profile.state,
        "country_code": runner.profile.country_code,
        "follower_count": accepted_follower_count(db, runner),
        "viewer_follow_status": follow.status if follow else None,
    }


def search_runners(db: Session, viewer: User, query: str) -> list[dict]:
    pattern = f"%{query.strip()}%"
    runners = db.scalars(
        select(User)
        .join(Profile)
        .join(PrivacySettings)
        .where(
            User.id != viewer.id,
            PrivacySettings.profile_visibility == "public",
            or_(Profile.username.ilike(pattern), Profile.display_name.ilike(pattern)),
        )
        .order_by(Profile.display_name)
        .limit(20)
    ).all()
    return [runner_summary(db, runner, viewer) for runner in runners]


def follower_overview(db: Session, viewer: User) -> dict[str, list[dict]]:
    pending = db.scalars(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == viewer.id, Follow.status == "pending")
        .order_by(Follow.created_at)
    ).all()
    followers = db.scalars(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == viewer.id, Follow.status == "accepted")
        .order_by(Follow.created_at.desc())
    ).all()
    following = db.scalars(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == viewer.id, Follow.status == "accepted")
        .order_by(Follow.created_at.desc())
    ).all()
    return {
        "pending": [runner_summary(db, runner, viewer) for runner in pending],
        "followers": [runner_summary(db, runner, viewer) for runner in followers],
        "following": [runner_summary(db, runner, viewer) for runner in following],
    }


def answer_follow_request(db: Session, viewer: User, username: str, accept: bool) -> None:
    follower = profile_user(db, username)
    if not follower:
        raise ValueError("not_found")
    follow = db.scalar(
        select(Follow).where(
            Follow.follower_id == follower.id, Follow.following_id == viewer.id
        )
    )
    if not follow or (accept and follow.status != "pending"):
        raise ValueError("not_found")
    if accept:
        follow.status = "accepted"
    else:
        db.delete(follow)
    db.commit()
