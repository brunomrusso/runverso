from fastapi import APIRouter

from app.services.oauth import provider_configured

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/auth")
def auth_config() -> dict[str, bool]:
    return {
        "google": provider_configured("google"),
        "strava": provider_configured("strava"),
    }
