from pydantic import BaseModel
from datetime import datetime
from app.schemas.track import TrackBrief


class PlaylistCreate(BaseModel):
    title: str
    description: str | None = None
    context: str = "general"


class PlaylistUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class PlaylistTrackOut(BaseModel):
    position: int
    track: TrackBrief

    model_config = {"from_attributes": True}


class PlaylistBrief(BaseModel):
    id: int
    title: str
    context: str
    source: str
    track_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class PlaylistOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    context: str
    source: str
    is_public: bool
    ai_prompt: str | None = None
    ai_explanation: str | None = None
    tracks: list[PlaylistTrackOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIPlaylistRequest(BaseModel):
    prompt: str
    context: str = "general"
