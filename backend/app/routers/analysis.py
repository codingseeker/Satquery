import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services import analysis_service, file_service
from app.utils.dependencies import get_current_user


settings = get_settings()
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_analysis(
    request: Request,
    file: UploadFile = File(...),
    query: str = Form(...),
    chat_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    original_filename, ext = file_service.validate_upload(file)
    file_service.enforce_upload_size(file)

    chat = analysis_service.get_owned_chat(db, chat_id, user)

    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty",
        )

    user_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
    os.makedirs(user_dir, exist_ok=True)

    temp_filename = f"upload_{os.urandom(16).hex()}.{ext}"
    dest = os.path.join(user_dir, temp_filename)

    try:
        size = file_service.stream_to_file_with_limit(file, dest)

        analysis = analysis_service.create_analysis(
            db,
            chat,
            user,
            query.strip(),
            original_filename,
            temp_filename,
        )

        analysis.stored_filename = temp_filename
        db.commit()
        db.refresh(analysis)

    except Exception:
        db.rollback()

        try:
            os.remove(dest)
        except FileNotFoundError:
            pass

        raise

    base_url = str(request.base_url).rstrip("/")

    return analysis_service.serialize_analysis(
        analysis,
        base_url,
    )


@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    analysis = analysis_service.get_owned_analysis(
        db,
        analysis_id,
        user,
    )

    base_url = str(request.base_url).rstrip("/")

    return analysis_service.serialize_analysis(
        analysis,
        base_url,
    )


@router.get("/{analysis_id}/file")
def get_analysis_file(
    analysis_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from fastapi.responses import FileResponse

    analysis = analysis_service.get_owned_analysis(
        db,
        analysis_id,
        user,
    )

    if not analysis.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis file not found",
        )

    file_path = os.path.join(
        settings.UPLOAD_DIR,
        str(analysis.user_id),
        analysis.stored_filename,
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis file not found",
        )

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=analysis.original_filename,
    )