from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.activities import router as activities_router
from app.api.auth import router as auth_router
from app.api.geography import router as geography_router
from app.api.health import router as health_router
from app.api.medals import router as medals_router
from app.api.profile import router as profile_router
from app.api.races import router as races_router
from app.api.status import router as status_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.environment != "local",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(activities_router)
app.include_router(auth_router)
app.include_router(geography_router)
app.include_router(health_router)
app.include_router(medals_router)
app.include_router(profile_router)
app.include_router(races_router)
app.include_router(status_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
