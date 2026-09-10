import os
import json
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.image import Image
from app.utils.dependencies import get_current_user
from app.services import file_service

settings = get_settings()
router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff"}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    original = file.filename or ""
    if original.strip() == "" or "." not in original:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid filename")

    ext = original.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    user_dir = os.path.join(settings.UPLOAD_DIR, f"images/{user.id}")
    os.makedirs(user_dir, exist_ok=True)

    content = await file.read()
    file_size = len(content)
    stored_name = f"{user.id}_{hash(original) & 0xFFFFFFFF}_{original}"
    stored_name = stored_name.replace("/", "_").replace("\\", "_")
    dest = os.path.join(user_dir, stored_name)

    with open(dest, "wb") as out:
        out.write(content)

    image = Image(
        user_id=user.id,
        original_filename=original,
        stored_filename=stored_name,
        content_type=file.content_type,
        file_size=file_size,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "image_id": str(image.id),
        "metadata": {
            "filename": original,
            "content_type": file.content_type,
            "file_size": file_size,
        },
    }


@router.get("/{image_id}/metadata")
def get_image_metadata(
    image_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image = db.query(Image).filter(Image.id == int(image_id), Image.user_id == user.id).first()
    if image is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "image_id": str(image.id),
        "filename": image.original_filename,
        "content_type": image.content_type,
        "file_size": image.file_size,
        "created_at": image.created_at.isoformat() if image.created_at else None,
    }


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image = db.query(Image).filter(Image.id == int(image_id), Image.user_id == user.id).first()
    if image is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")

    user_dir = os.path.join(settings.UPLOAD_DIR, f"images/{user.id}")
    dest = os.path.join(user_dir, image.stored_filename)
    if os.path.exists(dest):
        os.remove(dest)

    db.delete(image)
    db.commit()
    return None
