from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatOut
from app.utils.dependencies import get_current_user
from app.services.analysis_service import get_chat_analyses, get_owned_chat, serialize_analysis

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).all()


@router.post("", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(payload: ChatCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = Chat(user_id=user.id, title=payload.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned_chat(db, chat_id, user)


@router.get("/{chat_id}/analyses")
def list_chat_analyses(
    chat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = get_owned_chat(db, chat_id, user)
    analyses = get_chat_analyses(db, chat, user)
    base_url = str(request.base_url).rstrip("/")
    return [serialize_analysis(a, base_url) for a in analyses]


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = get_owned_chat(db, chat_id, user)
    db.delete(chat)
    db.commit()
    return None