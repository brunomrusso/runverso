import hashlib
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import engine
from app.dependencies.database import get_db
from app.main import app
from app.models import AuthIdentity, PrivacySettings, Profile, User, UserSession


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
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
