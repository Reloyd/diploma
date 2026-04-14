from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Enum, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.database import Base


class PlaylistContext(str, enum.Enum):
    work = "work"
    rest = "rest"
    sport = "sport"
    general = "general"


class PlaylistSource(str, enum.Enum):
    manual = "manual"
    ai = "ai"


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str] = mapped_column(String(20), default="general", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # reserved for future
    ai_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)  # original NL query
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # Claude explanation
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="playlists")
    tracks = relationship(
        "PlaylistTrack",
        back_populates="playlist",
        order_by="PlaylistTrack.position",
        cascade="all, delete-orphan",
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track", back_populates="playlist_tracks")
