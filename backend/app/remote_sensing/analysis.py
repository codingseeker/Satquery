"""Deterministic remote-sensing operations used before VLM reasoning."""
from __future__ import annotations
import os, math
from typing import Any, Dict, Optional
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.warp import transform_geom

from app.geospatial.raster_io import read_array, normalize_band, reproject_to_match, metadata


def _safe_index(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a.astype(np.float32) - b.astype(np.float32)) / (a + b + 1e-8)
    return out


def spectral_indices(path: str) -> Dict[str, Any]:
    arr, meta = read_array(path, max_size=1600)
    out: Dict[str, Any] = {}
    if arr.shape[0] >= 4:
        # Common convention: RGB + NIR. This is explicitly reported as an assumption.
        red, nir = arr[2], arr[3]
        ndvi = _safe_index(nir, red)
        out["ndvi_mean"] = float(np.nanmean(ndvi))
        out["ndvi_min"] = float(np.nanmin(ndvi))
        out["ndvi_max"] = float(np.nanmax(ndvi))
    if arr.shape[0] >= 5:
        # Common multispectral convention: band 5 as SWIR1.
        green, nir, swir = arr[1], arr[3], arr[4]
        ndwi = _safe_index(green, nir)
        mndwi = _safe_index(green, swir)
        out["ndwi_mean"] = float(np.nanmean(ndwi))
        out["mndwi_mean"] = float(np.nanmean(mndwi))
    return out


def sar_to_db(path: str, output_path: Optional[str] = None) -> str:
    """Convert linear SAR backscatter to dB; if already negative dB, keep it."""
    output_path = output_path or path + ".db.tif"
    with rasterio.open(path) as src:
        data = src.read().astype(np.float32)
        if np.nanpercentile(data, 50) > 0:
            data = 10 * np.log10(np.maximum(data, 1e-8))
        profile = src.profile.copy()
        profile.update(dtype="float32", nodata=np.nan)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)
    return output_path


def _rescale(arr):
    return np.stack([normalize_band(b) for b in arr], axis=0).astype(np.float32) / 255.0


def fuse_optical_sar(optical_path: str, sar_path: str, output_path: str) -> Dict[str, Any]:
    """Co-register SAR to optical grid and build a visualization + feature stack."""
    with rasterio.open(optical_path) as ref:
        optical_meta = metadata(optical_path)
        if not ref.crs:
            raise ValueError("Optical raster has no CRS")
    with rasterio.open(sar_path) as sar:
        sar_meta = metadata(sar_path)
        if not sar.crs:
            raise ValueError("SAR raster has no CRS")

    aligned_path = output_path + ".aligned.tif"
    reproject_to_match(sar_path, optical_path, aligned_path, Resampling.bilinear)
    opt, om = read_array(optical_path, max_size=1800)
    sar, _ = read_array(aligned_path, max_size=1800)
    optn, sarn = _rescale(opt), _rescale(sar)
    # RGB + SAR structural channel. Save four-band fused raster on optical grid.
    if optn.shape[0] >= 3:
        rgb = optn[:3]
    elif optn.shape[0] == 1:
        rgb = np.repeat(optn, 3, axis=0)
    else:
        rgb = np.concatenate([optn, np.zeros((3-optn.shape[0], *optn.shape[1:]), dtype=np.float32)])
    sar1 = sarn[0:1]
    fused = np.concatenate([rgb, sar1], axis=0)
    # Use a scaled preview-sized GeoTIFF; original CRS/grid are retained as metadata.
    with rasterio.open(optical_path) as src:
        profile = src.profile.copy()
        profile.update(count=4, dtype="float32", width=fused.shape[2], height=fused.shape[1], transform=src.transform * src.transform.scale(src.width/fused.shape[2], src.height/fused.shape[1]))
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(fused)
    return {"fused_path": output_path, "aligned_sar": aligned_path, "optical": optical_meta, "sar": sar_meta, "registration": {"target_crs": optical_meta["crs"], "target_shape": [optical_meta["height"], optical_meta["width"]], "method": "reproject+bilinear"}}


def change_detection(before_path: str, after_path: str, output_mask: str, threshold: Optional[float] = None) -> Dict[str, Any]:
    """Align T2 to T1 and calculate normalized multi-band change + GeoJSON regions."""
    aligned_after = after_path + ".aligned_to_before.tif"
    reproject_to_match(after_path, before_path, aligned_after, Resampling.bilinear)
    before, meta_b = read_array(before_path, max_size=2200)
    after, meta_a = read_array(aligned_after, max_size=2200)
    n = min(before.shape[0], after.shape[0])
    b = _rescale(before[:n])
    a = _rescale(after[:n])
    diff = np.sqrt(np.mean((a - b) ** 2, axis=0))
    if threshold is None:
        threshold = float(np.nanpercentile(diff, 90))
    mask = np.isfinite(diff) & (diff >= threshold)

    with rasterio.open(before_path) as src:
        transform = src.transform
        crs = src.crs
        # Approximate area from source pixel size; projected CRS gives square map units.
        pixel_area = abs(src.transform.a * src.transform.e)
        scale_x = src.width / diff.shape[1]
        scale_y = src.height / diff.shape[0]
        pixel_area *= scale_x * scale_y
        profile = src.profile.copy()
        profile.update(count=1, dtype="uint8", width=diff.shape[1], height=diff.shape[0], transform=src.transform * src.transform.scale(scale_x, scale_y), nodata=0)
        with rasterio.open(output_mask, "w", **profile) as dst:
            dst.write(mask.astype("uint8"), 1)
        geoms = []
        for geom, value in shapes(mask.astype("uint8"), mask=mask, transform=profile["transform"]):
            if value != 1:
                continue
            if crs and crs.to_epsg() != 4326:
                geom = transform_geom(crs, "EPSG:4326", geom, precision=7)
            geoms.append(geom)

    changed_pixels = int(mask.sum())
    changed_area = changed_pixels * pixel_area
    return {
        "mask_path": output_mask,
        "aligned_after": aligned_after,
        "threshold": threshold,
        "changed_pixels": changed_pixels,
        "changed_area_m2": float(changed_area) if (crs and crs.is_projected) else None,
        "changed_area_hectares": float(changed_area / 10000) if (crs and crs.is_projected) else None,
        "percentage_changed": float(mask.mean() * 100),
        "geojson": {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"change": "detected"}, "geometry": g} for g in geoms]},
        "metadata": {"before": meta_b, "after": meta_a, "crs": meta_b.get("crs")},
    }
