from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.services import analysis_service, file_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_analysis(
    request: Request,
    file: UploadFile = File(...),
    query: str = Form(...),
    chat_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = analysis_service.get_owned_chat(db, chat_id, user)
    if not query.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query must not be empty")

    original_filename, ext = file_service.validate_upload(file)
    analysis = analysis_service.create_analysis(
        db, chat, user, query.strip(), original_filename, "temp"
    )
    stored_filename = await file_service.save_upload(file, user, analysis.id, ext)
    analysis.stored_filename = stored_filename
    db.commit()
    db.refresh(analysis)

    analysis = analysis_service.run_analysis(db, analysis)
    base_url = str(request.base_url).rstrip("/")
    return analysis_service.serialize_analysis(analysis, base_url)


@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    analysis = analysis_service.get_owned_analysis(db, analysis_id, user)
    base_url = str(request.base_url).rstrip("/")
    return analysis_service.serialize_analysis(analysis, base_url)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    analysis = analysis_service.get_owned_analysis(db, analysis_id, user)
    file_service.delete_upload(user, analysis.stored_filename)
    db.delete(analysis)
    db.commit()
    return None


@router.get("/{analysis_id}/file")
def download_analysis_file(
    analysis_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    analysis = analysis_service.get_owned_analysis(db, analysis_id, user)
    dest = file_service.resolve_upload_path(user, analysis.stored_filename)
    media_type = file_service.media_type_for(analysis.stored_filename)
    return FileResponse(dest, media_type=media_type, filename=analysis.original_filename)