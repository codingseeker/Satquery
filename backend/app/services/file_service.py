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


def stream_to_file_with_limit(file: UploadFile, dest: str) -> int:
    """Synchronously stream an UploadFile to disk, enforcing MAX_FILE_SIZE. Returns bytes written."""
    import shutil
    size = 0
    chunk_size = 1024 * 1024  # 1MB
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    out.close()
                    if os.path.exists(dest):
                        os.remove(dest)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(dest):
            os.remove(dest)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    return size



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

def resolve_image_path(user: User, stored_filename: str) -> str:
    """Resolve files stored by /api/images without allowing path traversal."""
    user_dir = os.path.join(settings.UPLOAD_DIR, f"images/{user.id}")
    if not stored_filename or os.path.basename(stored_filename) != stored_filename:
        raise HTTPException(status_code=400, detail="Invalid file reference")
    dest = os.path.join(user_dir, stored_filename)
    if not os.path.isfile(dest):
        raise HTTPException(status_code=404, detail="File not found")
    return dest
