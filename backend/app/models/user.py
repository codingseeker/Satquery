from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True, default='SatQuery User')
    username = Column(String, nullable=True, default='@satquery_user')
    created_at = Column(DateTime, default=datetime.utcnow)
    chats = relationship('Chat', back_populates='user')
    analyses = relationship('Analysis', back_populates='user')
    images = relationship('Image', back_populates='user')



