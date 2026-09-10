from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIService(ABC):
    @abstractmethod
    def analyze(
        self,
        image_path: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass
