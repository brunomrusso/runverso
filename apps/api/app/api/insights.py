from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models import User
from app.schemas.insights import InsightsResponse
from app.services.insights import achievements, personal_records
from app.services.sessions import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightsResponse)
def runner_insights(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> InsightsResponse:
    record_items = personal_records(db, user)
    achievement_items = achievements(db, user)
    return InsightsResponse(
        records=record_items,
        achievements=achievement_items,
        unlocked_count=sum(item["unlocked"] for item in achievement_items),
        total_count=len(achievement_items),
    )
