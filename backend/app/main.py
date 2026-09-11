import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.routers import auth, analysis, chats, users, images, query, reports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SatQuery AI API",
    description="Satellite image analysis API powered by fine-tuned Qwen-VL.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:1000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(analysis.router)
app.include_router(users.router)
app.include_router(images.router)
app.include_router(query.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
def health():
    db_ok = True
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_ok = False
    return {"status": "ok", "database": "connected" if db_ok else "disconnected"}