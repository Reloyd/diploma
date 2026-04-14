from pydantic import BaseModel
from datetime import datetime
from app.schemas.track import TrackBrief


class RecommendationOut(BaseModel):
    id: int
    track: TrackBrief
    score: float
    reason_type: str
    reason_detail: str | None = None
    context: str
    created_at: datetime

    model_config = {"from_attributes": True}
