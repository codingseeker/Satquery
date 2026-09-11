"""Convert VLM pixel/normalized boxes into CRS-aware GeoJSON."""
from __future__ import annotations
from typing import Any, Dict, Iterable
import re
import rasterio
from rasterio.warp import transform_geom
from rasterio.crs import CRS

BOX_RE = re.compile(r"<box[^>]*>.*?(\d+)\D+(\d+)\D+(\d+)\D+(\d+)", re.I | re.S)

def parse_vlm_boxes(text: str, width: int, height: int) -> list[dict]:
    result = []
    for i, m in enumerate(BOX_RE.finditer(text or ""), 1):
        vals = list(map(int, m.groups()))
        # Qwen-style coordinates are normally 0..1000. Accept pixel boxes too.
        if max(vals) <= 1000 and (width > 1000 or height > 1000 or max(vals) > max(width, height) * 0.8):
            x1, y1, x2, y2 = [v / 1000 for v in vals]
            px1, py1, px2, py2 = x1 * width, y1 * height, x2 * width, y2 * height
        else:
            px1, py1, px2, py2 = vals
        px1, px2 = sorted((max(0, px1), min(width, px2)))
        py1, py2 = sorted((max(0, py1), min(height, py2)))
        result.append({"id": i, "label": f"Detection {i}", "pixel_bounds": {"xmin": px1, "ymin": py1, "xmax": px2, "ymax": py2}, "bounds": {"x": px1 / width * 100, "y": py1 / height * 100, "w": (px2-px1)/width*100, "h": (py2-py1)/height*100}})
    return result


def boxes_to_geojson(path: str, boxes: Iterable[dict], properties: dict | None = None) -> dict:
    features = []
    with rasterio.open(path) as src:
        for box in boxes:
            b = box["pixel_bounds"]
            corners = [
                rasterio.transform.xy(src.transform, b["ymin"], b["xmin"], offset="center"),
                rasterio.transform.xy(src.transform, b["ymin"], b["xmax"], offset="center"),
                rasterio.transform.xy(src.transform, b["ymax"], b["xmax"], offset="center"),
                rasterio.transform.xy(src.transform, b["ymax"], b["xmin"], offset="center"),
            ]
            geometry = {"type": "Polygon", "coordinates": [[list(corners[0]), list(corners[1]), list(corners[2]), list(corners[3]), list(corners[0])]]}
            if src.crs and src.crs != CRS.from_epsg(4326):
                geometry = transform_geom(src.crs, CRS.from_epsg(4326), geometry, precision=8)
            props = {"label": box.get("label"), **(properties or {})}
            features.append({"type": "Feature", "properties": props, "geometry": geometry})
    return {"type": "FeatureCollection", "features": features}
