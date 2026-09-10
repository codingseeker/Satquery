from typing import Any, Dict


class MockAIService:
    def analyze(self, query: str, filename: str) -> Dict[str, Any]:
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
            "confidence": 0.94,
            "answer": (
                "The uploaded satellite image has been successfully processed. "
                "Three regions were identified for further analysis."
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


mock_ai_service = MockAIService()