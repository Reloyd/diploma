from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.playlist import Playlist, PlaylistTrack
from app.models.track import Track, TrackGenre
from app.models.user import User
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate, AIPlaylistRequest
from app.services.deps import get_current_user
from app.services.ai_assistant import create_ai_playlist

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


def _playlist_query(user_id: int):
    return (
        select(Playlist)
        .options(
            selectinload(Playlist.tracks)
            .selectinload(PlaylistTrack.track)
            .selectinload(Track.artist),
            selectinload(Playlist.tracks)
            .selectinload(PlaylistTrack.track)
            .selectinload(Track.features),
        )
        .where(Playlist.user_id == user_id)
        .order_by(Playlist.created_at.desc())
    )


def _serialize_playlist(pl: Playlist) -> dict:
    tracks = sorted(pl.tracks, key=lambda pt: pt.position)
    return {
        "id": pl.id,
        "title": pl.title,
        "description": pl.description,
        "context": pl.context,
        "source": pl.source,
        "is_public": pl.is_public,
        "ai_prompt": pl.ai_prompt,
        "ai_explanation": pl.ai_explanation,
        "track_count": len(tracks),
        "tracks": [
            {
                "position": pt.position,
                "track": {
                    "id": pt.track.id,
                    "title": pt.track.title,
                    "artist_name": pt.track.artist.name if pt.track.artist else "",
                    "artist_id": pt.track.artist_id,
                    "cover_url": pt.track.cover_url,
                    "duration_sec": pt.track.duration_sec,
                    "file_url": pt.track.file_url,
                },
            }
            for pt in tracks
        ],
        "created_at": pl.created_at,
        "updated_at": pl.updated_at,
    }


@router.get("", response_model=list)
async def list_playlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    playlists = (await db.execute(_playlist_query(current_user.id))).scalars().unique().all()
    return [_serialize_playlist(pl) for pl in playlists]


@router.post("", response_model=dict, status_code=201)
async def create_playlist(
    data: PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = Playlist(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        context=data.context,
        source="manual",
    )
    db.add(pl)
    await db.flush()
    await db.refresh(pl)
    return {"id": pl.id, "title": pl.title, "context": pl.context, "source": pl.source}


@router.get("/{playlist_id}", response_model=dict)
async def get_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = (await db.execute(
        _playlist_query(current_user.id).where(Playlist.id == playlist_id)
    )).scalar_one_or_none()
    if not pl:
        raise HTTPException(404, "Playlist not found")
    return _serialize_playlist(pl)


@router.patch("/{playlist_id}", response_model=dict)
async def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = (await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )).scalar_one_or_none()
    if not pl:
        raise HTTPException(404, "Playlist not found")
    if data.title is not None:
        pl.title = data.title
    if data.description is not None:
        pl.description = data.description
    await db.commit()
    return {"id": pl.id, "title": pl.title, "description": pl.description}


@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = (await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )).scalar_one_or_none()
    if not pl:
        raise HTTPException(404, "Playlist not found")
    await db.delete(pl)


@router.post("/{playlist_id}/tracks/{track_id}", status_code=204)
async def add_track(
    playlist_id: int,
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = (await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )).scalar_one_or_none()
    if not pl:
        raise HTTPException(404, "Playlist not found")

    track = (await db.execute(select(Track).where(Track.id == track_id))).scalar_one_or_none()
    if not track:
        raise HTTPException(404, "Track not found")

    count = (await db.execute(
        select(func.count()).where(PlaylistTrack.playlist_id == playlist_id)
    )).scalar_one()

    db.add(PlaylistTrack(playlist_id=playlist_id, track_id=track_id, position=count))


@router.delete("/{playlist_id}/tracks/{track_id}", status_code=204)
async def remove_track(
    playlist_id: int,
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pl = (await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )).scalar_one_or_none()
    if not pl:
        raise HTTPException(404, "Playlist not found")

    pt = (await db.execute(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id,
        )
    )).scalar_one_or_none()
    if pt:
        await db.delete(pt)


@router.post("/ai/create", response_model=dict, status_code=201)
async def create_ai_playlist_endpoint(
    data: AIPlaylistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a playlist using AI assistant based on natural language prompt."""
    playlist = await create_ai_playlist(db, current_user.id, data.prompt, data.context)
    return _serialize_playlist(playlist)
