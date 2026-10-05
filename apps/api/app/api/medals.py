import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.database import get_db
from app.models import Medal, MedalPhoto, Race, User
from app.schemas.medal import (
    MedalCreate,
    MedalListResponse,
    MedalPhotoResponse,
    MedalRaceResponse,
    MedalResponse,
    MedalUpdate,
)
from app.services.images import delete_upload, resolve_upload, save_medal_photo
from app.services.sessions import get_current_user

router = APIRouter(tags=["medals"])


def owned_medal(db: Session, user: User, medal_id: uuid.UUID) -> Medal:
    medal = db.scalar(
        select(Medal)
        .options(selectinload(Medal.race), selectinload(Medal.photos))
        .where(Medal.id == medal_id, Medal.user_id == user.id)
    )
    if not medal:
        raise HTTPException(status_code=404, detail="Medalha não encontrada")
    return medal


def medal_response(medal: Medal) -> MedalResponse:
    return MedalResponse(
        id=medal.id,
        title=medal.title,
        story=medal.story,
        is_favorite=medal.is_favorite,
        visibility=medal.visibility,
        race=MedalRaceResponse(
            id=medal.race.id,
            event_name=medal.race.event_name,
            race_date=medal.race.race_date.isoformat(),
            category=medal.race.category,
            city=medal.race.city,
            state=medal.race.state,
        ),
        photos=[
            MedalPhotoResponse(
                id=photo.id,
                kind=photo.kind,
                content_type=photo.content_type,
                sort_order=photo.sort_order,
                image_url=f"/medal-photos/{photo.id}",
                thumbnail_url=f"/medal-photos/{photo.id}?thumbnail=true",
            )
            for photo in medal.photos
        ],
    )


@router.post("/medals", response_model=MedalResponse, status_code=status.HTTP_201_CREATED)
def create_medal(
    payload: MedalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MedalResponse:
    race = db.scalar(select(Race).where(Race.id == payload.race_id, Race.user_id == user.id))
    if not race:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    if race.medal:
        raise HTTPException(status_code=409, detail="Esta prova já possui uma medalha")
    medal = Medal(user_id=user.id, **payload.model_dump())
    db.add(medal)
    db.commit()
    return medal_response(owned_medal(db, user, medal.id))


@router.get("/medals", response_model=MedalListResponse)
def list_medals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MedalListResponse:
    medals = db.scalars(
        select(Medal)
        .options(selectinload(Medal.race), selectinload(Medal.photos))
        .where(Medal.user_id == user.id)
        .order_by(desc(Medal.is_favorite), desc(Medal.created_at))
    ).all()
    return MedalListResponse(items=[medal_response(item) for item in medals], total=len(medals))


@router.get("/medals/count")
def medal_count(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, int]:
    total = db.scalar(select(func.count()).select_from(Medal).where(Medal.user_id == user.id)) or 0
    return {"total": total}


@router.patch("/medals/{medal_id}", response_model=MedalResponse)
def update_medal(
    medal_id: uuid.UUID,
    payload: MedalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MedalResponse:
    medal = owned_medal(db, user, medal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(medal, field, value)
    db.commit()
    return medal_response(owned_medal(db, user, medal.id))


@router.post("/medals/{medal_id}/photos", response_model=MedalResponse)
async def upload_medal_photo(
    medal_id: uuid.UUID,
    kind: str = Form(default="gallery", pattern="^(front|back|gallery)$"),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MedalResponse:
    medal = owned_medal(db, user, medal_id)
    file_path, thumbnail_path, size_bytes, content_type = await save_medal_photo(
        photo, user.id, medal.id
    )
    if kind in {"front", "back"}:
        previous = next((item for item in medal.photos if item.kind == kind), None)
        if previous:
            delete_upload(previous.file_path)
            delete_upload(previous.thumbnail_path)
            db.delete(previous)
    db.add(
        MedalPhoto(
            medal_id=medal.id,
            kind=kind,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            content_type=content_type,
            size_bytes=size_bytes,
            sort_order=len(medal.photos),
        )
    )
    db.commit()
    return medal_response(owned_medal(db, user, medal.id))


@router.get("/medal-photos/{photo_id}")
def medal_photo(
    photo_id: uuid.UUID,
    thumbnail: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponse:
    photo = db.scalar(
        select(MedalPhoto)
        .join(Medal)
        .where(MedalPhoto.id == photo_id, Medal.user_id == user.id)
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    path = resolve_upload(photo.thumbnail_path if thumbnail else photo.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, media_type=photo.content_type)


@router.delete("/medal-photos/{photo_id}", status_code=204)
def delete_medal_photo(
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    photo = db.scalar(
        select(MedalPhoto)
        .join(Medal)
        .where(MedalPhoto.id == photo_id, Medal.user_id == user.id)
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    delete_upload(photo.file_path)
    delete_upload(photo.thumbnail_path)
    db.delete(photo)
    db.commit()


@router.delete("/medals/{medal_id}", status_code=204)
def delete_medal(
    medal_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    medal = owned_medal(db, user, medal_id)
    for photo in medal.photos:
        delete_upload(photo.file_path)
        delete_upload(photo.thumbnail_path)
    db.delete(medal)
    db.commit()
