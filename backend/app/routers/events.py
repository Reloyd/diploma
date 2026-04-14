from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.events import PlayEvent
from app.models.ratings import ImplicitRating
from app.models.user import User
from app.schemas.events import PlayEventCreate
from app.services.deps import get_current_user
from app.tasks import recalculate_ratings_task

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", status_code=201)
async def record_event(
    data: PlayEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = PlayEvent(
        user_id=current_user.id,
        track_id=data.track_id,
        played_seconds=data.played_seconds,
        played_ratio=data.played_ratio,
        skipped=data.skipped,
        repeated=data.repeated,
        liked=data.liked,
        context=data.context,
    )
    db.add(event)
    await db.commit()

    # Queue async recalculation
    recalculate_ratings_task.delay(current_user.id, data.track_id)

    return {"status": "recorded"}
