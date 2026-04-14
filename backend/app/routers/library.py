from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.library import UserLibrary
from app.models.track import Track, TrackGenre, Genre
from app.models.user import User
from app.services.deps import get_current_user
from app.routers.tracks import _track_query, _enrich_with_library, _build_track_out

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("", response_model=dict)
async def get_library(
    genre: str | None = Query(None),
    artist_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = _track_query().join(UserLibrary, Track.id == UserLibrary.track_id).where(
        UserLibrary.user_id == current_user.id
    )
    if genre:
        stmt = stmt.join(TrackGenre).join(Genre).where(Genre.name.ilike(f"%{genre}%"))
    if artist_id:
        stmt = stmt.where(Track.artist_id == artist_id)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    tracks = (await db.execute(stmt.offset((page - 1) * per_page).limit(per_page))).scalars().unique().all()

    library_ids = [t.id for t in tracks]  # all are in library
    items = [_build_track_out(t, library_ids) for t in tracks]
    return {"total": total, "page": page, "per_page": per_page, "items": items}


@router.post("/{track_id}", status_code=204)
async def add_to_library(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check track exists
    track = (await db.execute(select(Track).where(Track.id == track_id))).scalar_one_or_none()
    if not track:
        raise HTTPException(404, "Track not found")

    existing = (await db.execute(
        select(UserLibrary).where(and_(UserLibrary.user_id == current_user.id, UserLibrary.track_id == track_id))
    )).scalar_one_or_none()

    if not existing:
        db.add(UserLibrary(user_id=current_user.id, track_id=track_id))


@router.delete("/{track_id}", status_code=204)
async def remove_from_library(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (await db.execute(
        select(UserLibrary).where(and_(UserLibrary.user_id == current_user.id, UserLibrary.track_id == track_id))
    )).scalar_one_or_none()
    if entry:
        await db.delete(entry)
