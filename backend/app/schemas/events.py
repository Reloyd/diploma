from pydantic import BaseModel
from datetime import datetime


class PlayEventCreate(BaseModel):
    track_id: int
    played_seconds: float = 0.0
    played_ratio: float = 0.0
    skipped: bool = False
    repeated: bool = False
    liked: bool = False
    context: str = "general"
