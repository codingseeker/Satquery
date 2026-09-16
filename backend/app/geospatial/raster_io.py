"""Native raster/GeoTIFF IO and spatial metadata utilities."""
from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional, Tuple
import numpy as np
import rasterio

try:
    import xarray as xr
    import rioxarray as rxr
except Exception:
    xr = None
    rxr = None
try:
    from osgeo import gdal
except Exception:
    gdal = None
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
from rasterio.transform import rowcol, xy
from rasterio.crs import CRS


def is_raster(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in {".tif", ".tiff", ".geotiff"}


def metadata(path: str) -> Dict[str, Any]:
    with rasterio.open(path) as src:
        crs = src.crs.to_string() if src.crs else None
        return {
            "driver": src.driver,
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0] if src.dtypes else None,
            "crs": crs,
            "crs_wkt": src.crs.to_wkt() if src.crs else None,
            "transform": list(src.transform),
            "bounds": {"left": src.bounds.left, "bottom": src.bounds.bottom, "right": src.bounds.right, "top": src.bounds.top},
            "resolution": list(src.res),
            "nodata": src.nodata,
            "units": list(src.units) if src.units else None,
            "descriptions": list(src.descriptions) if src.descriptions else None,
            "band_indexes": list(src.indexes),
            "is_georeferenced": bool(src.crs and src.transform),
            "geospatial_stack": {"rasterio": True, "xarray": xr is not None, "rioxarray": rxr is not None, "gdal": gdal is not None},
        }


def read_array(path: str, bands: Optional[list[int]] = None, max_size: int = 2048) -> Tuple[np.ndarray, Dict[str, Any]]:
    with rasterio.open(path) as src:
        indexes = bands or list(src.indexes)
        scale = min(1.0, max_size / max(src.width, src.height))
        out_h = max(1, int(src.height * scale))
        out_w = max(1, int(src.width * scale))
        arr = src.read(indexes, out_shape=(len(indexes), out_h, out_w), resampling=Resampling.bilinear)
        profile = metadata(path)
        profile["preview_scale"] = scale
        profile["preview_shape"] = [out_h, out_w]
        return arr, profile


def normalize_band(band: np.ndarray, low: float = 2, high: float = 98) -> np.ndarray:
    x = np.asarray(band, dtype=np.float32)
    finite = np.isfinite(x)
    if not finite.any():
        return np.zeros(x.shape, dtype=np.uint8)
    lo, hi = np.nanpercentile(x[finite], [low, high])
    if hi <= lo:
        hi = lo + 1.0
    y = np.clip((x - lo) / (hi - lo), 0, 1)
    return (y * 255).astype(np.uint8)


def render_preview(path: str, output_path: str) -> str:
    from PIL import Image
    arr, _ = read_array(path, max_size=1800)
    if arr.shape[0] == 1:
        rgb = np.stack([normalize_band(arr[0])] * 3, axis=-1)
    elif arr.shape[0] == 2:
        a, b = normalize_band(arr[0]), normalize_band(arr[1])
        rgb = np.stack([a, b, b], axis=-1)
    else:
        rgb = np.stack([normalize_band(arr[0]), normalize_band(arr[1]), normalize_band(arr[2])], axis=-1)
    Image.fromarray(rgb, mode="RGB").save(output_path, format="PNG", optimize=True)
    return output_path


def pixel_to_crs(path: str, row: float, col: float) -> Dict[str, float]:
    with rasterio.open(path) as src:
        x, y = xy(src.transform, row, col, offset="center")
        return {"x": float(x), "y": float(y)}


def crs_to_pixel(path: str, x: float, y: float) -> Dict[str, float]:
    with rasterio.open(path) as src:
        r, c = rowcol(src.transform, x, y)
        return {"row": float(r), "col": float(c)}


def bounds_geojson(path: str) -> Dict[str, Any]:
    with rasterio.open(path) as src:
        b = src.bounds
        coords = [[
            [b.left, b.bottom], [b.left, b.top], [b.right, b.top], [b.right, b.bottom], [b.left, b.bottom]
        ]]
        return {"type": "Polygon", "coordinates": coords}


def reproject_to_match(src_path: str, reference_path: str, output_path: str, resampling: Resampling = Resampling.bilinear) -> str:
    with rasterio.open(reference_path) as ref, rasterio.open(src_path) as src:
        if not ref.crs or not src.crs:
            raise ValueError("Both rasters must have a CRS for reprojection/co-registration")
        profile = ref.profile.copy()
        profile.update(count=src.count, dtype=src.dtypes[0], nodata=src.nodata)
        with rasterio.open(output_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i), destination=rasterio.band(dst, i),
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=ref.transform, dst_crs=ref.crs,
                    dst_width=ref.width, dst_height=ref.height, resampling=resampling,
                )
    return output_path


def to_wgs84_geometry(path: str, geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a geometry expressed in the raster CRS into WGS84 GeoJSON."""
    from rasterio.warp import transform_geom
    with rasterio.open(path) as src:
        if not src.crs:
            return geometry
        return transform_geom(src.crs, CRS.from_epsg(4326), geometry, precision=8)
