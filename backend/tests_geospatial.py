import os
import tempfile
import numpy as np
import rasterio
from rasterio.transform import from_origin
import pytest

from app.geospatial.raster_io import metadata, pixel_to_crs, crs_to_pixel
from app.remote_sensing.analysis import change_detection

@pytest.fixture
def mock_geotiff(tmp_path):
    path = os.path.join(tmp_path, "mock_satellite.tif")
    # Simulate a Sentinel-2 optical tile
    profile = dict(
        driver="GTiff", width=100, height=100, count=4, dtype="float32",
        crs="EPSG:4326", transform=from_origin(75.0, 15.0, 0.0001, 0.0001)
    )
    # 4 Bands: B, G, R, NIR
    arr = np.random.rand(4, 100, 100).astype("float32")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr)
    return path, arr

def test_geotiff_metadata_extraction(mock_geotiff):
    path, _ = mock_geotiff
    md = metadata(path)
    
    # Confirm it returns valid EPSG coordinates without crashing
    assert "EPSG:4326" in md["crs"]
    assert md["count"] == 4
    assert md["width"] == 100
    assert md["height"] == 100

def test_geotiff_band_arrays(mock_geotiff):
    path, original_arr = mock_geotiff
    with rasterio.open(path) as src:
        bands = src.read()
        # Confirm it loads the exact band arrays
        assert bands.shape == (4, 100, 100)
        np.testing.assert_array_almost_equal(bands, original_arr)

def test_pixel_to_crs_projection(mock_geotiff):
    path, _ = mock_geotiff
    xy = pixel_to_crs(path, 50, 50)
    px = crs_to_pixel(path, xy["x"], xy["y"])
    assert abs(px["row"] - 50) <= 1
    assert abs(px["col"] - 50) <= 1

if __name__ == "__main__":
    pytest.main(["-v", __file__])
