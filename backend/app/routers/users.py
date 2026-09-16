from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserOut
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

class UserUpdate(BaseModel):
    full_name: str | None = None
    username: str | None = None

@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user

@router.put("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.username is not None:
        # Note: In a real app we'd check for username collisions here.
        user.username = payload.username
    db.commit()
    db.refresh(user)
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(user)
    db.commit()
    return None
