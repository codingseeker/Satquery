from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    query = Column(String)
    original_filename = Column(String)
    stored_filename = Column(String, nullable=True)
    task = Column(String, nullable=True)
    status = Column(String)
    confidence = Column(Float, nullable=True)
    answer = Column(String, nullable=True)
    result_json = Column(String, nullable=True)
    stats = Column(JSON, nullable=True)
    regions = Column(JSON, nullable=True)
    map = Column(JSON, nullable=True)
    layers = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    chat = relationship('Chat', back_populates='analyses')
    user = relationship('User', back_populates='analyses')

