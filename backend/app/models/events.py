from sqlalchemy import ForeignKey, Float, Boolean, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class PlayEvent(Base):
    """Records a single user-track interaction event."""
    __tablename__ = "play_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)

    # How many seconds were actually played
    played_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Fraction of track that was played (0-1)
    played_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Was the track skipped before finishing?
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Was the track explicitly repeated?
    repeated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Explicit like
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Listening context: work / rest / sport / general
    context: Mapped[str] = mapped_column(String(20), default="general", nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user = relationship("User", back_populates="play_events")
    track = relationship("Track", back_populates="play_events")
