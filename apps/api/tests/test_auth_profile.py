import hashlib
import io
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import engine
from app.dependencies.database import get_db
from app.main import app
from app.models import (
    Activity,
    AuthIdentity,
    PrivacySettings,
    Profile,
    Race,
    StravaConnection,
    User,
    UserSession,
)
from app.services.geography import geography_summary, process_activity_locations
from app.services.oauth import find_or_create_strava_user
from app.services.races import classify_activity, distance_category


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def authenticated_client(db: Session) -> TestClient:
    user = User(email="runner@example.com")
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name="Runner"))
    db.add(PrivacySettings(user_id=user.id))
    db.add(AuthIdentity(user_id=user.id, provider="google", provider_user_id="google-1"))
    token = "test-session-token"
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    db.commit()
    client = TestClient(app)
    client.cookies.set(get_settings().session_cookie_name, token)
    return client


def test_me_requires_authentication() -> None:
    response = TestClient(app).get("/me")

    assert response.status_code == 401


def test_auth_config_exposes_only_provider_availability() -> None:
    response = TestClient(app).get("/config/auth")

    assert response.status_code == 200
    assert set(response.json()) == {"google", "strava"}
    assert all(isinstance(value, bool) for value in response.json().values())


def test_authenticated_user_completes_onboarding(authenticated_client: TestClient) -> None:
    response = authenticated_client.patch(
        "/me/profile",
        json={
            "username": "corredor_10k",
            "real_name": "Corredor Teste",
            "display_name": "Corredor",
            "bio": None,
            "city": "São Paulo",
            "state": "SP",
            "country_code": "br",
            "started_running_year": 2020,
            "favorite_distance": "10K",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["username"] == "corredor_10k"
    assert data["profile"]["country_code"] == "BR"
    assert data["profile"]["onboarding_completed"] is True
    assert data["providers"] == ["google"]


def test_strava_is_linked_without_creating_duplicate_user(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    token = {
        "athlete": {
            "id": 12345,
            "firstname": "Runner",
            "lastname": "Teste",
            "city": "São Paulo",
            "state": "SP",
        },
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_at": int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
    }

    user_count = db.scalar(select(func.count()).select_from(User))
    linked_user = find_or_create_strava_user(db, token, target_user=user)

    assert linked_user.id == user.id
    assert db.scalar(select(func.count()).select_from(User)) == user_count
    assert db.get(StravaConnection, user.id).athlete_id == "12345"
    assert {identity.provider for identity in user.identities} == {"google", "strava"}


def test_strava_already_linked_to_another_user_is_rejected(
    db: Session, authenticated_client: TestClient
) -> None:
    first_user = db.scalar(select(User).where(User.email == "runner@example.com"))
    token = {
        "athlete": {"id": 67890, "firstname": "Runner"},
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_at": int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
    }
    find_or_create_strava_user(db, token, target_user=first_user)
    second_user = User(email="second@example.com")
    db.add(second_user)
    db.flush()

    with pytest.raises(ValueError, match="outro usuário"):
        find_or_create_strava_user(db, token, target_user=second_user)


def test_activity_stats_are_private_to_authenticated_user(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    db.add(
        Activity(
            user_id=user.id,
            source="strava",
            external_id="activity-1",
            name="Corrida matinal",
            sport_type="Run",
            distance_meters=10000,
            moving_time_seconds=3600,
            elapsed_time_seconds=3700,
            elevation_gain=80,
            started_at=datetime.now(UTC),
            source_visibility="everyone",
            local_visibility="private",
            raw_payload={"id": "activity-1"},
        )
    )
    db.commit()

    stats = authenticated_client.get("/activities/stats")
    activities = authenticated_client.get("/activities")

    assert stats.status_code == 200
    assert stats.json()["total"] == 1
    assert stats.json()["total_distance_meters"] == 10000
    assert activities.status_code == 200
    assert activities.json()["items"][0]["local_visibility"] == "private"
    assert TestClient(app).get("/activities").status_code == 401


def test_strava_race_tag_creates_high_confidence_suggestion(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    activity = Activity(
        user_id=user.id,
        source="strava",
        external_id="race-activity",
        name="Maratona da Cidade",
        sport_type="Run",
        workout_type=1,
        distance_meters=42180,
        moving_time_seconds=14400,
        elapsed_time_seconds=14500,
        elevation_gain=100,
        started_at=datetime.now(UTC),
        source_visibility="everyone",
        local_visibility="private",
        raw_payload={"id": "race-activity", "workout_type": 1},
    )
    classify_activity(activity)
    db.add(activity)
    db.commit()

    suggestions = authenticated_client.get("/race-suggestions")

    assert suggestions.status_code == 200
    suggestion = next(item for item in suggestions.json() if item["id"] == str(activity.id))
    assert suggestion["confidence"] == "high"
    assert suggestion["suggested_category"] == "42K"
    assert "Marcada como prova no Strava" in suggestion["reasons"]

    confirmed = authenticated_client.post(
        f"/race-suggestions/{activity.id}/confirm",
        json={"visibility": "private", "country_code": "BR"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["category"] == "42K"
    assert authenticated_client.get("/races/count").json() == {"total": 1}


def test_marathon_gps_overage_is_not_classified_as_ultra() -> None:
    assert distance_category(42278).name == "42K"
    assert distance_category(44200).name == "42K"
    assert distance_category(50000).name == "ULTRA"


def test_medal_photo_is_private_and_thumbnail_is_generated(
    authenticated_client: TestClient,
) -> None:
    race = authenticated_client.post(
        "/races",
        json={
            "event_name": "Corrida Medalha",
            "race_date": "2026-01-10",
            "category": "5K",
            "official_distance_meters": 5000,
            "country_code": "BR",
            "visibility": "private",
        },
    ).json()
    medal_response = authenticated_client.post(
        "/medals",
        json={"race_id": race["id"], "title": "Minha medalha", "visibility": "private"},
    )
    assert medal_response.status_code == 201
    medal = medal_response.json()
    image_bytes = io.BytesIO()
    Image.new("RGB", (800, 600), "orange").save(image_bytes, format="JPEG")

    upload = authenticated_client.post(
        f"/medals/{medal['id']}/photos",
        data={"kind": "front"},
        files={"photo": ("medal.jpg", image_bytes.getvalue(), "image/jpeg")},
    )

    assert upload.status_code == 200
    photo = upload.json()["photos"][0]
    assert authenticated_client.get(photo["thumbnail_url"]).status_code == 200
    assert TestClient(app).get(photo["thumbnail_url"]).status_code == 401
    assert authenticated_client.get("/medals/count").json() == {"total": 1}
    assert authenticated_client.delete(f"/medals/{medal['id']}").status_code == 204


def test_geography_uses_offline_city_centroids_instead_of_raw_coordinates(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    activity = Activity(
        user_id=user.id,
        source="strava",
        external_id="geo-activity",
        name="Corrida em São Paulo",
        sport_type="Run",
        distance_meters=5000,
        moving_time_seconds=1800,
        elapsed_time_seconds=1900,
        elevation_gain=30,
        started_at=datetime.now(UTC),
        start_latitude=-23.55052,
        start_longitude=-46.633308,
        source_visibility="everyone",
        local_visibility="private",
        raw_payload={"id": "geo-activity"},
    )
    db.add(activity)
    db.commit()

    result = process_activity_locations(db, user)
    summary = geography_summary(db, user, "training")

    assert result["processed"] == 1
    assert summary["country_count"] >= 1
    assert any(country["country_code"] == "BR" for country in summary["countries"])
    point = next(point for point in summary["points"] if point["country_code"] == "BR")
    assert (point["latitude"], point["longitude"]) != (-23.55052, -46.633308)
    assert TestClient(app).get("/geography/summary").status_code == 401


def test_public_profile_hides_real_name_by_default(authenticated_client: TestClient) -> None:
    authenticated_client.patch(
        "/me/profile",
        json={
            "username": "perfil_publico",
            "real_name": "Nome Privado",
            "display_name": "Nome Público",
            "bio": None,
            "city": None,
            "state": None,
            "country_code": "BR",
            "started_running_year": None,
            "favorite_distance": None,
        },
    )

    response = authenticated_client.get("/users/perfil_publico")

    assert response.status_code == 200
    assert response.json()["display_name"] == "Nome Público"
    assert response.json()["real_name"] is None


def test_insights_select_best_race_times_and_unlock_achievements(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    db.add_all(
        [
            Race(
                user_id=user.id,
                event_name="10K rápido",
                race_date=datetime.now(UTC).date(),
                category="10K",
                official_distance_meters=10000,
                net_time_seconds=3000,
            ),
            Race(
                user_id=user.id,
                event_name="10K lento",
                race_date=datetime.now(UTC).date(),
                category="10K",
                official_distance_meters=10000,
                net_time_seconds=3200,
            ),
            Race(
                user_id=user.id,
                event_name="Maratona",
                race_date=datetime.now(UTC).date(),
                category="42K",
                official_distance_meters=42195,
                net_time_seconds=14400,
            ),
            Race(
                user_id=user.id,
                event_name="Sem tempo oficial",
                race_date=datetime.now(UTC).date(),
                category="5K",
                official_distance_meters=5000,
                net_time_seconds=None,
            ),
        ]
    )
    db.commit()

    response = authenticated_client.get("/insights")

    assert response.status_code == 200
    data = response.json()
    records = {item["category"]: item for item in data["records"]}
    assert records["10K"]["event_name"] == "10K rápido"
    assert records["10K"]["pace_seconds_per_km"] == 300
    assert "5K" not in records
    unlocked = {item["code"]: item["unlocked"] for item in data["achievements"]}
    assert unlocked["first_race"] is True
    assert unlocked["first_marathon"] is True
    assert TestClient(app).get("/insights").status_code == 401


def test_public_profile_overview_respects_privacy(
    db: Session, authenticated_client: TestClient
) -> None:
    user = db.scalar(select(User).where(User.email == "runner@example.com"))
    user.profile.username = "corredor_publico"
    user.profile.display_name = "Corredor Público"
    user.privacy_settings.profile_visibility = "public"
    user.privacy_settings.races_visibility = "public"
    user.privacy_settings.medals_visibility = "private"
    user.privacy_settings.locations_visibility = "private"
    db.add(
        Race(
            user_id=user.id,
            event_name="10K público",
            race_date=datetime.now(UTC).date(),
            category="10K",
            official_distance_meters=10000,
            net_time_seconds=3000,
        )
    )
    db.commit()

    response = TestClient(app).get("/community/corredor_publico")

    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["display_name"] == "Corredor Público"
    assert data["race_count"] == 1
    assert data["records"][0]["event_name"] == "10K público"
    assert data["medal_count"] is None
    assert data["country_count"] is None


def test_private_profile_is_not_public(authenticated_client: TestClient) -> None:
    authenticated_client.patch(
        "/me/profile",
        json={
            "username": "perfil_privado",
            "real_name": None,
            "display_name": "Privado",
            "bio": None,
            "city": None,
            "state": None,
            "country_code": "BR",
            "started_running_year": None,
            "favorite_distance": None,
        },
    )
    privacy = {
        "profile_visibility": "private",
        "activities_visibility": "private",
        "races_visibility": "public",
        "medals_visibility": "public",
        "photos_visibility": "followers",
        "locations_visibility": "followers",
        "show_real_name": False,
        "show_times": True,
        "approve_followers": True,
    }
    assert authenticated_client.patch("/me/privacy", json=privacy).status_code == 200

    response = authenticated_client.get("/users/perfil_privado")

    assert response.status_code == 404
