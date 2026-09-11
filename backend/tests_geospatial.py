"""Small smoke tests for the geospatial pipeline.
Run from backend/: python tests_geospatial.py
"""
import os, tempfile
import numpy as np
import rasterio
from rasterio.transform import from_origin
from app.geospatial.raster_io import metadata, pixel_to_crs, crs_to_pixel
from app.remote_sensing.analysis import change_detection

with tempfile.TemporaryDirectory() as d:
    a = os.path.join(d, "before.tif"); b = os.path.join(d, "after.tif"); m = os.path.join(d, "change.tif")
    profile = dict(driver="GTiff", width=100, height=100, count=3, dtype="float32", crs="EPSG:32643", transform=from_origin(500000, 1500000, 10, 10))
    before = np.ones((3,100,100), dtype="float32")
    after = before.copy(); after[:, 40:60, 40:60] = 2
    for p, arr in [(a,before),(b,after)]:
        with rasterio.open(p,"w",**profile) as dst: dst.write(arr)
    md = metadata(a)
    assert md["crs"] == "EPSG:32643" and md["count"] == 3
    xy = pixel_to_crs(a, 50, 50); px = crs_to_pixel(a, xy["x"], xy["y"])
    assert abs(px["row"]-50) <= 1 and abs(px["col"]-50) <= 1
    result = change_detection(a,b,m,threshold=0.1)
    assert result["changed_pixels"] > 0
    assert result["changed_area_hectares"] > 0
print("geospatial smoke tests passed")
