from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Runneverso API"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://runverso:runverso_local@localhost:5432/runverso"
    cors_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    session_secret: str = "change-me-in-local-env"
    session_cookie_name: str = "runverso_session"
    session_days: int = 30
    google_client_id: str = ""
    google_client_secret: str = ""
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_sync_max_pages: int = 20
    token_encryption_secret: str = "change-me-in-local-env"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
