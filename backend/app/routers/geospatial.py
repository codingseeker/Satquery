import os, tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.image import Image
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.services.file_service import resolve_image_path
from app.geospatial.raster_io import metadata, pixel_to_crs, crs_to_pixel, bounds_geojson
from app.geospatial.query_router import route_query
from app.remote_sensing.analysis import spectral_indices, fuse_optical_sar, change_detection
from app.config import get_settings

settings = get_settings(); router = APIRouter(prefix="/api/geospatial", tags=["geospatial"])

class PixelPoint(BaseModel): image_id: int; row: float; col: float
class CRSPoint(BaseModel): image_id: int; x: float; y: float
class FusionRequest(BaseModel): optical_image_id: int; sar_image_id: int
class ChangeRequest(BaseModel): before_image_id: int; after_image_id: int; threshold: Optional[float] = Field(default=None, ge=0)


def owned(db, user, iid):
    obj = db.query(Image).filter(Image.id == iid, Image.user_id == user.id).first()
    if not obj: raise HTTPException(404, f"Image {iid} not found")
    return resolve_image_path(user, obj.stored_filename), obj

@router.get("/metadata/{image_id}")
def get_raster_metadata(image_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, _ = owned(db, user, image_id); return metadata(path)

@router.post("/pixel-to-crs")
def pixel_to_crs_endpoint(body: PixelPoint, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, _ = owned(db, user, body.image_id); return pixel_to_crs(path, body.row, body.col)

@router.post("/crs-to-pixel")
def crs_to_pixel_endpoint(body: CRSPoint, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, _ = owned(db, user, body.image_id); return crs_to_pixel(path, body.x, body.y)

@router.get("/footprint/{image_id}")
def footprint(image_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, _ = owned(db, user, image_id); return {"type": "Feature", "properties": {"image_id": image_id}, "geometry": bounds_geojson(path)}

@router.get("/indices/{image_id}")
def indices(image_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    path, _ = owned(db, user, image_id); return spectral_indices(path)

@router.post("/fusion")
def fusion(body: FusionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    optical, _ = owned(db, user, body.optical_image_id); sar, _ = owned(db, user, body.sar_image_id)
    out_dir = os.path.join(settings.UPLOAD_DIR, "derived", str(user.id)); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"fusion_{body.optical_image_id}_{body.sar_image_id}.tif")
    try: result = fuse_optical_sar(optical, sar, out)
    except Exception as exc: raise HTTPException(422, str(exc))
    result["task"] = "OPTICAL_SAR_FUSION"; return result

@router.post("/change-detection")
def change(body: ChangeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    before, _ = owned(db, user, body.before_image_id); after, _ = owned(db, user, body.after_image_id)
    out_dir = os.path.join(settings.UPLOAD_DIR, "derived", str(user.id)); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"change_{body.before_image_id}_{body.after_image_id}.tif")
    try: result = change_detection(before, after, out, body.threshold)
    except Exception as exc: raise HTTPException(422, str(exc))
    result["task"] = "TEMPORAL_CHANGE_DETECTION"; return result

@router.post("/route-query")
def route(body: dict, user: User = Depends(get_current_user)):
    return route_query(str(body.get("query", "")), int(body.get("image_count", 1)))
