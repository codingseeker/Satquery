import os
from dotenv import load_dotenv

# Ensure .env is loaded so standalone os.environ.get() works
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')), override=True)

from ai_service.base import AIService
from ai_service.mock_service import MockAIService
from ai_service.multiagent_service import MultiAgentService

_service_instance = None

def get_ai_service() -> AIService:
    global _service_instance
    if _service_instance is not None:
        return _service_instance

    mode = os.environ.get("AI_MODE", "mock").lower()
    
    # HARD OVERRIDE: If the trained model exists on disk, force real mode
    # to avoid any environment variable shadowing bugs
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    expected_model_path = os.path.join(root_dir, "training", "models", "satquery-best-lora")
    if os.path.exists(expected_model_path):
        print("FORCE OVERRIDE: Found trained model. Using RealAIService.")
        mode = "real"

    if mode == "mock":
        _service_instance = MockAIService()
    elif mode == "multiagent":
        use_real = os.environ.get("MULTIAGENT_USE_REAL", "false").lower() == "true"
        _service_instance = MultiAgentService(use_real_model=use_real)
    elif mode == "real":
        model_path = os.environ.get("MODEL_PATH", "training/models/satquery-best-lora")
        from ai_service.real_service import RealAIService
        _service_instance = RealAIService(model_path=model_path)
    else:
        raise ValueError(f"Unknown AI_MODE: {mode}. Supported: mock, real, multiagent")
    
    return _service_instance
