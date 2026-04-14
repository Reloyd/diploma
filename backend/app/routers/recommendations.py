from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.recommendation import Recommendation
from app.models.track import Track, TrackGenre
from app.models.library import UserLibrary
from app.models.user import User
from app.services.deps import get_current_user
from app.tasks import build_recommendations_task

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=list)
async def get_recommendations(
    context: str = Query("general"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Recommendation)
        .options(
            selectinload(Recommendation.track).selectinload(Track.artist),
            selectinload(Recommendation.track).selectinload(Track.features),
        )
        .where(Recommendation.user_id == current_user.id)
        .order_by(desc(Recommendation.score))
        .limit(limit)
    )
    if context != "general":
        stmt = stmt.where(Recommendation.context == context)

    recs = (await db.execute(stmt)).scalars().all()

    # Fetch which of these tracks are in the user's library
    track_ids = [r.track_id for r in recs]
    library_stmt = select(UserLibrary.track_id).where(
        UserLibrary.user_id == current_user.id,
        UserLibrary.track_id.in_(track_ids),
    )
    in_library_ids = set((await db.execute(library_stmt)).scalars().all())

    result = []
    for r in recs:
        t = r.track
        result.append({
            "id": r.id,
            "track": {
                "id": t.id,
                "title": t.title,
                "artist_name": t.artist.name if t.artist else "",
                "artist_id": t.artist_id,
                "cover_url": t.cover_url,
                "duration_sec": t.duration_sec,
                "file_url": t.file_url,
                "in_library": t.id in in_library_ids,
            },
            "score": r.score,
            "reason_type": r.reason_type,
            "reason_detail": r.reason_detail,
            "context": r.context,
            "created_at": r.created_at,
        })
    return result


@router.post("/refresh", status_code=202)
async def refresh_recommendations(
    context: str = Query("general"),
    current_user: User = Depends(get_current_user),
):
    """Trigger async recalculation of recommendations."""
    build_recommendations_task.delay(current_user.id, context)
    return {"status": "queued"}
