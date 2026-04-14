from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.track import Track, Artist, Album, Genre, TrackGenre
from app.models.library import UserLibrary
from app.models.user import User
from app.schemas.track import TrackOut, ArtistOut, AlbumOut, GenreOut
from app.services.deps import get_current_user

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


def _track_query():
    return (
        select(Track)
        .options(
            selectinload(Track.artist),
            selectinload(Track.album),
            selectinload(Track.genres).selectinload(TrackGenre.genre),
            selectinload(Track.features),
        )
    )


async def _enrich_with_library(tracks: list[Track], user_id: int, db: AsyncSession) -> list[int]:
    if not tracks:
        return []
    ids = [t.id for t in tracks]
    result = await db.execute(
        select(UserLibrary.track_id).where(
            and_(UserLibrary.user_id == user_id, UserLibrary.track_id.in_(ids))
        )
    )
    return list(result.scalars())


def _build_track_out(track: Track, library_ids: list[int]) -> dict:
    genres = [{"id": tg.genre.id, "name": tg.genre.name} for tg in track.genres if tg.genre]
    artist = {"id": track.artist.id, "name": track.artist.name, "image_url": track.artist.image_url}
    album = None
    if track.album:
        album = {"id": track.album.id, "title": track.album.title, "artist_id": track.album.artist_id,
                 "cover_url": track.album.cover_url, "release_year": track.album.release_year}
    features = None
    if track.features:
        f = track.features
        features = {"tempo": f.tempo, "beat_strength": f.beat_strength, "rms_energy": f.rms_energy,
                    "spectral_centroid": f.spectral_centroid, "energy_level": f.energy_level,
                    "danceability": f.danceability, "valence": f.valence}
    return {
        "id": track.id,
        "title": track.title,
        "artist": artist,
        "album": album,
        "genres": genres,
        "duration_sec": track.duration_sec,
        "file_url": track.file_url,
        "cover_url": track.cover_url,
        "features": features,
        "in_library": track.id in library_ids,
        "created_at": track.created_at,
    }


@router.get("", response_model=dict)
async def list_tracks(
    q: str | None = Query(None),
    genre: str | None = Query(None),
    artist_id: int | None = Query(None),
    album_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = _track_query()

    if q:
        stmt = stmt.where(
            Track.title.ilike(f"%{q}%")
        )
    if genre:
        stmt = stmt.join(TrackGenre).join(Genre).where(Genre.name.ilike(f"%{genre}%"))
    if artist_id:
        stmt = stmt.where(Track.artist_id == artist_id)
    if album_id:
        stmt = stmt.where(Track.album_id == album_id)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page).order_by(Track.id)
    tracks = (await db.execute(stmt)).scalars().unique().all()

    library_ids = await _enrich_with_library(list(tracks), current_user.id, db)
    items = [_build_track_out(t, library_ids) for t in tracks]

    return {"total": total, "page": page, "per_page": per_page, "items": items}


@router.get("/{track_id}", response_model=dict)
async def get_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = _track_query().where(Track.id == track_id)
    track = (await db.execute(stmt)).scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    library_ids = await _enrich_with_library([track], current_user.id, db)
    return _build_track_out(track, library_ids)


# --- Artists ---

@router.get("/artists/list", response_model=dict)
async def list_artists(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Artist)
    if q:
        stmt = stmt.where(Artist.name.ilike(f"%{q}%"))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    artists = (await db.execute(stmt.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return {"total": total, "items": [ArtistOut.model_validate(a) for a in artists]}


@router.get("/artists/{artist_id}", response_model=dict)
async def get_artist(
    artist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = (await db.execute(select(Artist).where(Artist.id == artist_id))).scalar_one_or_none()
    if not artist:
        raise HTTPException(404, "Artist not found")

    # Get albums
    albums = (await db.execute(select(Album).where(Album.artist_id == artist_id))).scalars().all()
    # Get tracks count
    track_count = (await db.execute(
        select(func.count()).where(Track.artist_id == artist_id)
    )).scalar_one()

    return {
        "artist": ArtistOut.model_validate(artist),
        "albums": [AlbumOut.model_validate(a) for a in albums],
        "track_count": track_count,
    }


# --- Albums ---

@router.get("/albums/{album_id}", response_model=dict)
async def get_album(
    album_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album = (await db.execute(
        select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
    )).scalar_one_or_none()
    if not album:
        raise HTTPException(404, "Album not found")

    stmt = _track_query().where(Track.album_id == album_id).order_by(Track.id)
    tracks = (await db.execute(stmt)).scalars().unique().all()
    library_ids = await _enrich_with_library(list(tracks), current_user.id, db)

    return {
        "album": AlbumOut.model_validate(album),
        "artist": ArtistOut.model_validate(album.artist),
        "tracks": [_build_track_out(t, library_ids) for t in tracks],
    }


# --- Genres ---

@router.get("/genres/list", response_model=list)
async def list_genres(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    genres = (await db.execute(select(Genre).order_by(Genre.name))).scalars().all()
    return [GenreOut.model_validate(g) for g in genres]
