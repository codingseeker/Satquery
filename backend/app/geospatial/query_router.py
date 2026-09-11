"""Natural-language query -> deterministic remote-sensing workflow."""
import re

def route_query(query: str, image_count: int = 1) -> dict:
    q = query.lower()
    change = any(x in q for x in ["change", "changed", "before and after", "temporal", "increase", "decrease", "difference"])
    sar = any(x in q for x in ["sar", "radar", "backscatter", "sentinel-1"])
    optical = any(x in q for x in ["optical", "multispectral", "sentinel-2", "ndvi", "ndwi", "vegetation", "water"])
    fusion = sar and optical and image_count >= 2
    if change and image_count >= 2:
        task = "TEMPORAL_CHANGE_DETECTION"
    elif fusion:
        task = "OPTICAL_SAR_FUSION"
    elif sar:
        task = "SAR_ANALYSIS"
    elif optical:
        task = "OPTICAL_ANALYSIS"
    else:
        task = "VISUAL_QUESTION_ANSWERING"
    return {"task": task, "requires_temporal": change and image_count >= 2, "requires_sar": sar, "requires_optical": optical, "requires_fusion": fusion}
