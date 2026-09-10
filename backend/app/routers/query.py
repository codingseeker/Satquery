import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.chat import Chat
from app.models.image import Image
from app.models.analysis import Analysis
from app.utils.dependencies import get_current_user
from ai_service.factory import get_ai_service

settings = get_settings()
router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    conversation_id: str
    query: str
    image_ids: List[str] = []


def _resolve_image_path(user_id: int, image: Image) -> str:
    user_dir = os.path.join(settings.UPLOAD_DIR, f"images/{user_id}")
    return os.path.join(user_dir, image.stored_filename)


@router.post("/query")
async def handle_query(
    body: QueryRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        chat_id = int(body.conversation_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid conversation_id")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    images = []
    image_path = None
    if body.image_ids:
        images = (
            db.query(Image)
            .filter(Image.id.in_([int(i) for i in body.image_ids if i.isdigit()]), Image.user_id == user.id)
            .all()
        )
        if images:
            image_path = _resolve_image_path(user.id, images[0])

    if image_path is None:
        image_path = ""

    ai_service = get_ai_service()
    result = ai_service.analyze(image_path, body.query)

    analysis = Analysis(
        chat_id=chat.id,
        user_id=user.id,
        query=body.query,
        original_filename=images[0].original_filename if images else "",
        stored_filename=images[0].stored_filename if images else "",
        task=result.get("task"),
        status=result.get("status", "completed"),
        confidence=result.get("confidence"),
        answer=result.get("answer", ""),
        result_json=json.dumps(result),
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    base_url = str(request.base_url).rstrip("/")
    return {
        "id": analysis.id,
        "chat_id": analysis.chat_id,
        "query": analysis.query,
        "task": result.get("task", ""),
        "task_label": result.get("task", "").replace("_", " ").title(),
        "status": analysis.status,
        "confidence": result.get("confidence", 0),
        "answer": result.get("answer", ""),
        "stats": result.get("stats", {}),
        "regions": result.get("regions", []),
        "changes": result.get("changes", []),
        "images": result.get("images", []),
        "metadata": result.get("metadata", {}),
        "execution": result.get("execution", {}),
        "map": result.get("map", {}),
        "layers": result.get("layers", {}),
        "image_url": f"{base_url}/api/analysis/{analysis.id}/file" if analysis.stored_filename else None,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
    }


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in chats
    ]


@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        chat_id = int(conv_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    analyses = (
        db.query(Analysis)
        .filter(Analysis.chat_id == chat.id, Analysis.user_id == user.id)
        .order_by(Analysis.created_at.asc())
        .all()
    )

    messages = []
    for a in analyses:
        result = json.loads(a.result_json) if a.result_json else {}
        messages.append({
            "role": "user",
            "content": a.query,
            "timestamp": a.created_at.isoformat() if a.created_at else None,
        })
        messages.append({
            "role": "assistant",
            "content": a.answer or "",
            "analysis": {
                "task": a.task,
                "task_label": (a.task or "").replace("_", " ").title(),
                "confidence": a.confidence,
                "answer": a.answer,
                "stats": result.get("stats"),
                "regions": result.get("regions", []),
                "changes": result.get("changes", []),
                "execution": result.get("execution"),
            },
            "timestamp": a.completed_at.isoformat() if a.completed_at else None,
        })

    return {
        "id": str(chat.id),
        "title": chat.title,
        "messages": messages,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
    }


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        chat_id = int(conv_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(chat)
    db.commit()
    return None
