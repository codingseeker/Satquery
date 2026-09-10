import os
from typing import Any, Dict, Optional
from ai_service.base import AIService


class RealAIService(AIService):
    def __init__(self, model_path: str = ""):
        self.model_path = model_path
        self.model = None
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. "
                "Place your trained model files there and set MODEL_PATH in .env."
            )
        self._loaded = True

    def analyze(
        self,
        image_path: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._load_model()
        raise NotImplementedError(
            "RealAIService inference not yet implemented. "
            "Add your model loading and inference code in ai_service/real_service.py."
        )
