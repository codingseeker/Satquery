from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.analysis import Analysis
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    conversation_id: str
    analysis_id: str


@router.post("")
def request_report(
    body: ReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        analysis_id = int(body.analysis_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid analysis_id")

    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id, Analysis.user_id == user.id
    ).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    base_url = str(request.base_url).rstrip("/")
    download_url = f"{base_url}/api/analysis/{analysis.id}/file"
    return {"download_url": download_url}
