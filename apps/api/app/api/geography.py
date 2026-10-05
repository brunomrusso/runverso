from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models import User
from app.schemas.geography import GeographyResponse
from app.services.geography import geography_summary, process_activity_locations
from app.services.sessions import get_current_user

router = APIRouter(prefix="/geography", tags=["geography"])


@router.post("/process")
def process_geography(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, int]:
    return process_activity_locations(db, user)


@router.get("/summary", response_model=GeographyResponse)
def get_geography_summary(
    mode: Literal["training", "races"] = "training",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return geography_summary(db, user, mode)
