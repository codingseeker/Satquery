import json
import os
from datetime import datetime
from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.models.chat import Chat
from app.models.user import User
from ai_service.factory import get_ai_service


def get_owned_chat(db: Session, chat_id: int, user: User) -> Chat:
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


def create_analysis(db: Session, chat: Chat, user: User, query: str, original_filename: str, stored_filename: str) -> Analysis:
    analysis = Analysis(
        chat_id=chat.id,
        user_id=user.id,
        query=query,
        original_filename=original_filename,
        stored_filename=stored_filename,
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def run_analysis(db: Session, analysis: Analysis) -> Analysis:
    ai_service = get_ai_service()
    image_path = ""
    if analysis.stored_filename:
        from app.config import get_settings
        settings = get_settings()
        image_path = os.path.join(settings.UPLOAD_DIR, str(analysis.user_id), analysis.stored_filename)
    result = ai_service.analyze(image_path, analysis.query)
    analysis.task = result["task"]
    analysis.status = result["status"]
    analysis.confidence = result["confidence"]
    analysis.answer = result["answer"]
    analysis.result_json = json.dumps(result)
    analysis.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(analysis)
    return analysis


def get_owned_analysis(db: Session, analysis_id: int, user: User) -> Analysis:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


def get_chat_analyses(db: Session, chat: Chat, user: User) -> list:
    return (
        db.query(Analysis)
        .filter(Analysis.chat_id == chat.id, Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )


def serialize_analysis(analysis: Analysis, base_url: str) -> Dict[str, Any]:
    extra = {}
    if analysis.result_json:
        extra = json.loads(analysis.result_json)
    return {
        "id": analysis.id,
        "chat_id": analysis.chat_id,
        "user_id": analysis.user_id,
        "query": analysis.query,
        "original_filename": analysis.original_filename,
        "task": analysis.task,
        "status": analysis.status,
        "confidence": analysis.confidence,
        "answer": analysis.answer,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
        "stats": extra.get("stats"),
        "regions": extra.get("regions", []),
        "map": extra.get("map", {"center": [12.9716, 77.5946], "bounds": []}),
        "layers": extra.get("layers", {"optical": None, "sar": None, "changes": None}),
        "image_url": f"{base_url}/api/analysis/{analysis.id}/file",
    }