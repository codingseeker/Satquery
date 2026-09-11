import os
from dotenv import load_dotenv

# Ensure .env is loaded so standalone os.environ.get() works
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')), override=True)

from ai_service.base import AIService

_service_instance = None

def get_ai_service() -> AIService:
    global _service_instance
    if _service_instance is not None:
        return _service_instance

    model_path = os.environ.get("MODEL_PATH", "training/models/satquery-best-lora")
    from ai_service.real_service import RealAIService
    _service_instance = RealAIService(model_path=model_path)
    
    return _service_instance
