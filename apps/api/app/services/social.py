from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Comment,
    Follow,
    Medal,
    Notification,
    PrivacySettings,
    Profile,
    Race,
    Reaction,
    User,
)
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


def notify(db: Session, user: User, actor: User, kind: str, message: str) -> None:
    if user.id != actor.id:
        db.add(Notification(user_id=user.id, actor_id=actor.id, kind=kind, message=message))


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
        notify(
            db,
            runner,
            viewer,
            "follow_request" if status == "pending" else "new_follower",
            (
                "pediu para seguir você"
                if status == "pending"
                else "começou a seguir você"
            ),
        )
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
        "avatar_url": runner.profile.avatar_url,
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


def community_feed(db: Session, viewer: User) -> list[dict]:
    followed_ids = db.scalars(
        select(Follow.following_id).where(
            Follow.follower_id == viewer.id, Follow.status == "accepted"
        )
    ).all()
    if not followed_ids:
        return []

    races = db.scalars(
        select(Race)
        .join(User, Race.user_id == User.id)
        .join(Profile, Profile.user_id == User.id)
        .join(PrivacySettings, PrivacySettings.user_id == User.id)
        .where(
            Race.user_id.in_(followed_ids),
            Race.visibility.in_(["public", "followers"]),
            PrivacySettings.races_visibility.in_(["public", "followers"]),
            PrivacySettings.profile_visibility == "public",
        )
        .order_by(Race.created_at.desc())
        .limit(40)
    ).all()
    medals = db.scalars(
        select(Medal)
        .join(User, Medal.user_id == User.id)
        .join(Profile, Profile.user_id == User.id)
        .join(PrivacySettings, PrivacySettings.user_id == User.id)
        .where(
            Medal.user_id.in_(followed_ids),
            Medal.visibility.in_(["public", "followers"]),
            PrivacySettings.medals_visibility.in_(["public", "followers"]),
            PrivacySettings.profile_visibility == "public",
        )
        .order_by(Medal.created_at.desc())
        .limit(40)
    ).all()

    items = [
        {
            "id": str(race.id),
            "target_type": "race",
            "target_id": str(race.id),
            "kind": "race",
            "username": race.user.profile.username,
            "display_name": race.user.profile.display_name,
            "title": race.event_name,
            "subtitle": (
                f"completou uma prova {race.category}"
                + (f" em {race.city}" if race.city else "")
            ),
            "happened_at": race.created_at.isoformat(),
        }
        for race in races
    ] + [
        {
            "id": str(medal.id),
            "target_type": "medal",
            "target_id": str(medal.id),
            "kind": "medal",
            "username": medal.user.profile.username,
            "display_name": medal.user.profile.display_name,
            "title": medal.title or medal.race.event_name,
            "subtitle": f"guardou uma medalha {medal.race.category}",
            "happened_at": medal.created_at.isoformat(),
        }
        for medal in medals
    ]
    for item in items:
        item["like_count"] = reaction_count(db, item["target_type"], item["target_id"])
        item["comment_count"] = comment_count(db, item["target_type"], item["target_id"])
        item["viewer_liked"] = bool(
            db.scalar(
                select(Reaction.id).where(
                    Reaction.user_id == viewer.id,
                    Reaction.target_type == item["target_type"],
                    Reaction.target_id == item["target_id"],
                )
            )
        )
    return sorted(items, key=lambda item: item["happened_at"], reverse=True)[:40]


def reaction_count(db: Session, target_type: str, target_id) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Reaction)
        .where(Reaction.target_type == target_type, Reaction.target_id == target_id)
    ) or 0


def comment_count(db: Session, target_type: str, target_id) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Comment)
        .where(Comment.target_type == target_type, Comment.target_id == target_id)
    ) or 0


def visible_target(db: Session, viewer: User, target_type: str, target_id):
    model = {"race": Race, "medal": Medal}.get(target_type)
    if model is None:
        raise ValueError("not_found")
    target = db.get(model, target_id)
    if not target or target.user_id == viewer.id:
        raise ValueError("not_found")
    owner = target.user
    follow = follow_state(db, viewer, owner)
    setting = owner.privacy_settings.races_visibility
    if target_type == "medal":
        setting = owner.privacy_settings.medals_visibility
    if not can_view(owner, viewer, setting, follow) or target.visibility == "private":
        raise ValueError("not_found")
    return target, owner


def toggle_reaction(db: Session, viewer: User, target_type: str, target_id) -> tuple[bool, int]:
    _target, owner = visible_target(db, viewer, target_type, target_id)

    existing = db.scalar(
        select(Reaction).where(
            Reaction.user_id == viewer.id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
    )
    liked = existing is None
    if existing:
        db.delete(existing)
    else:
        db.add(Reaction(user_id=viewer.id, target_type=target_type, target_id=target_id))
        event = "prova" if target_type == "race" else "medalha"
        notify(db, owner, viewer, "reaction", f"curtiu sua {event}")
    db.commit()
    return liked, reaction_count(db, target_type, target_id)


def comment_items(db: Session, viewer: User, target_type: str, target_id) -> list[dict]:
    target, owner = visible_target(db, viewer, target_type, target_id)
    comments = db.scalars(
        select(Comment)
        .where(Comment.target_type == target_type, Comment.target_id == target_id)
        .order_by(Comment.created_at.asc())
        .limit(50)
    ).all()
    return [
        {
            "id": str(comment.id),
            "body": comment.body,
            "username": comment.user.profile.username,
            "display_name": comment.user.profile.display_name,
            "avatar_url": comment.user.profile.avatar_url,
            "can_delete": comment.user_id == viewer.id or owner.id == viewer.id,
            "created_at": comment.created_at.isoformat(),
        }
        for comment in comments
        if comment.user.profile
    ] if target else []


def add_comment(
    db: Session, viewer: User, target_type: str, target_id, body: str
) -> tuple[dict, int]:
    target, owner = visible_target(db, viewer, target_type, target_id)
    clean_body = " ".join(body.strip().split())
    if not clean_body or len(clean_body) > 500:
        raise ValueError("invalid_comment")
    comment = Comment(
        user_id=viewer.id,
        target_type=target_type,
        target_id=target_id,
        body=clean_body,
    )
    db.add(comment)
    event = "prova" if target_type == "race" else "medalha"
    notify(db, owner, viewer, "comment", f"comentou sua {event}")
    db.commit()
    return {
        "id": str(comment.id),
        "body": comment.body,
        "username": viewer.profile.username,
        "display_name": viewer.profile.display_name,
        "avatar_url": viewer.profile.avatar_url,
        "can_delete": True,
        "created_at": comment.created_at.isoformat(),
    }, comment_count(db, target_type, target_id)


def delete_comment(db: Session, viewer: User, comment_id) -> None:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise ValueError("not_found")
    target, owner = visible_target(db, viewer, comment.target_type, comment.target_id)
    if not target or (comment.user_id != viewer.id and owner.id != viewer.id):
        raise ValueError("not_found")
    db.delete(comment)
    db.commit()


def notifications(db: Session, viewer: User) -> tuple[list[dict], int]:
    items = db.scalars(
        select(Notification)
        .where(Notification.user_id == viewer.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
    ).all()
    unread = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == viewer.id, Notification.is_read.is_(False))
    ) or 0
    return [
        {
            "id": str(item.id),
            "kind": item.kind,
            "message": item.message,
            "actor_username": item.actor.profile.username if item.actor else None,
            "actor_display_name": item.actor.profile.display_name if item.actor else None,
            "is_read": item.is_read,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ], unread


def mark_notifications_read(db: Session, viewer: User) -> None:
    items = db.scalars(
        select(Notification).where(
            Notification.user_id == viewer.id, Notification.is_read.is_(False)
        )
    ).all()
    for item in items:
        item.is_read = True
    db.commit()


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
        notify(db, follower, viewer, "follow_accepted", "aceitou sua solicitação")
    else:
        db.delete(follow)
    db.commit()
