from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AnalysisOut(BaseModel):
    id: int
    chat_id: int
    user_id: int
    query: str
    original_filename: str
    task: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    answer: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    stats: Optional[Dict[str, Any]] = None
    regions: Optional[List[Any]] = None
    map: Optional[Dict[str, Any]] = None
    layers: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisResult(BaseModel):
    id: int
    chat_id: int
    query: str
    task: str
    status: str
    confidence: float
    answer: str
    stats: Dict[str, Any]
    regions: List[Any] = []
    map: Dict[str, Any]
    layers: Dict[str, Any]
    image_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None