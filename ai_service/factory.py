import os
from ai_service.base import AIService
from ai_service.mock_service import MockAIService


def get_ai_service() -> AIService:
    mode = os.environ.get("AI_MODE", "mock").lower()
    if mode == "mock":
        return MockAIService()
    if mode == "real":
        model_path = os.environ.get("MODEL_PATH", "")
        if not model_path:
            raise ValueError("AI_MODE=real requires MODEL_PATH to be set")
        from ai_service.real_service import RealAIService
        return RealAIService(model_path=model_path)
    raise ValueError(f"Unknown AI_MODE: {mode}. Supported: mock, real")
