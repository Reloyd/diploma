from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.routers import auth, tracks, library, events, recommendations, playlists


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MinIO buckets on startup
    try:
        from app.services.minio_client import ensure_buckets
        ensure_buckets()
    except Exception as e:
        print(f"MinIO init warning: {e}")
    yield
    await engine.dispose()


app = FastAPI(
    title="Phonoteka API",
    description="Personal music library web application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tracks.router)
app.include_router(library.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(playlists.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
