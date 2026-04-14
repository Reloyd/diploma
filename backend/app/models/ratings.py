from sqlalchemy import ForeignKey, Float, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class ImplicitRating(Base):
    """Aggregated implicit rating for user-track pair, recalculated by ML worker."""
    __tablename__ = "implicit_ratings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)

    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # 0-1 normalised
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_played_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skip_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="implicit_ratings")
    track = relationship("Track", back_populates="implicit_ratings")


class UserArtistPreference(Base):
    """Aggregated preference score for user-artist pair."""
    __tablename__ = "user_artist_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="artist_preferences")
    artist = relationship("Artist")


class UserGenrePreference(Base):
    """Aggregated preference score for user-genre pair."""
    __tablename__ = "user_genre_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="genre_preferences")
    genre = relationship("Genre", back_populates="user_genre_preferences")
