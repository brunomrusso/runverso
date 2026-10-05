import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings

settings = get_settings()
Image.MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _rgb_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, "white")
        alpha = image.getchannel("A")
        background.paste(image.convert("RGB"), mask=alpha)
        return background
    return image.convert("RGB")


async def save_medal_photo(
    upload: UploadFile, user_id: uuid.UUID, medal_id: uuid.UUID
) -> tuple[str, str, int, str]:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Use uma imagem JPEG, PNG ou WebP")
    content = await upload.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="A imagem deve ter no máximo 10 MB")
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.verify()
        with Image.open(io.BytesIO(content)) as source:
            image = _rgb_image(source)
            image.thumbnail((3000, 3000), Image.Resampling.LANCZOS)
            thumbnail = image.copy()
            thumbnail.thumbnail((500, 500), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise HTTPException(
            status_code=422, detail="O arquivo não contém uma imagem válida"
        ) from exc

    directory = Path(settings.upload_directory) / str(user_id) / str(medal_id)
    directory.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    image_path = directory / f"{file_id}.jpg"
    thumbnail_path = directory / f"{file_id}_thumb.jpg"
    image.save(image_path, "JPEG", quality=90, optimize=True)
    thumbnail.save(thumbnail_path, "JPEG", quality=82, optimize=True)
    base = Path(settings.upload_directory)
    return (
        str(image_path.relative_to(base)),
        str(thumbnail_path.relative_to(base)),
        image_path.stat().st_size,
        "image/jpeg",
    )


def resolve_upload(relative_path: str) -> Path:
    base = Path(settings.upload_directory).resolve()
    path = (base / relative_path).resolve()
    if base not in path.parents:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return path


def delete_upload(relative_path: str) -> None:
    path = resolve_upload(relative_path)
    if path.exists():
        path.unlink()
