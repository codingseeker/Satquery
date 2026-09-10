import os
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from app.config import get_settings
from app.models.user import User

settings = get_settings()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_upload(file: UploadFile) -> Tuple[str, str]:
    original = file.filename or ""
    if original.strip() == "" or "." not in original:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    ext = original.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return original, ext


async def save_upload(file: UploadFile, user: User, analysis_id: int, ext: str) -> str:
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
    os.makedirs(user_dir, exist_ok=True)
    stored_name = f"{analysis_id}.{ext}"
    dest = os.path.join(user_dir, stored_name)
    size = 0
    chunk_size = 1024 * 1024
    try:
        with open(dest, "wb") as out:
            while chunk := await file.read(chunk_size):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
                out.write(chunk)
    except HTTPException:
        if os.path.exists(dest):
            os.remove(dest)
        raise
    return stored_name


def resolve_upload_path(user: User, stored_filename: str) -> str:
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
    separators = [sep for sep in (os.sep, os.altsep) if sep]
    if not stored_filename or any(sep in stored_filename for sep in separators):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file reference")
    dest = os.path.join(user_dir, stored_filename)
    if not os.path.exists(dest) or not os.path.isfile(dest):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return dest


def media_type_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tif": "image/tiff",
        "tiff": "image/tiff",
    }.get(ext, "application/octet-stream")


def delete_upload(user: User, stored_filename: str) -> None:
    try:
        dest = resolve_upload_path(user, stored_filename)
        os.remove(dest)
    except HTTPException:
        pass