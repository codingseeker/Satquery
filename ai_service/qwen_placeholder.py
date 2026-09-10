from typing import Any, Dict, Optional
from ai_service.base import AIService


class QwenAIService(AIService):
    def analyze(
        self,
        image_path: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "QwenAIService is not available on this machine. "
            "Set AI_MODE=mock or deploy to a machine with LORE + Qwen models."
        )
