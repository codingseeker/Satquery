from typing import Any, Dict, Optional
from ai_service.base import AIService


class MockAIService(AIService):
    def analyze(
        self,
        image_path: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        lower = query.lower()
        if "water" in lower or "water body" in lower:
            task = "Water Detection"
        elif "built" in lower or "urban" in lower or "built-up" in lower:
            task = "Built-up Detection"
        elif "change" in lower or "compare" in lower or "two image" in lower:
            task = "Change Detection"
        else:
            task = "Scene Understanding"

        return {
            "task": task,
            "status": "completed",
            "confidence": 0.87,
            "answer": (
                "Mock analysis completed. The satellite image was processed "
                "using a placeholder service. No real AI model was invoked."
            ),
            "stats": {
                "built_up": "42.8 ha",
                "vegetation": "31.2 ha",
                "water": "12.1 ha",
            },
            "regions": [
                {"id": 1, "label": "Region 01", "type": "vegetation"},
                {"id": 2, "label": "Region 02", "type": "built-up"},
                {"id": 3, "label": "Region 03", "type": "water"},
            ],
            "changes": [],
            "images": [],
            "metadata": {
                "source": "mock",
                "model": "placeholder",
                "image_path": image_path,
            },
            "execution": {
                "task_detected": task,
                "tools": ["MockAIService"],
                "input_type": "satellite_image",
                "status": "completed",
                "duration_ms": 42,
                "output_type": "analysis_report",
            },
            "map": {
                "center": [12.9716, 77.5946],
                "bounds": [[12.965, 77.585], [12.979, 77.607]],
            },
            "layers": {
                "optical": None,
                "sar": None,
                "changes": None,
            },
        }
