from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    jamendo_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", back_populates="artist")


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jamendo_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    track_genres = relationship("TrackGenre", back_populates="genre")
    user_genre_preferences = relationship("UserGenrePreference", back_populates="genre")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), nullable=False)
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id", ondelete="SET NULL"), nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    license_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jamendo_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    features_extracted: Mapped[bool] = mapped_column(default=False)

    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")
    genres = relationship("TrackGenre", back_populates="track", cascade="all, delete-orphan")
    features = relationship("TrackFeature", back_populates="track", uselist=False, cascade="all, delete-orphan")
    library_entries = relationship("UserLibrary", back_populates="track", cascade="all, delete-orphan")
    playlist_tracks = relationship("PlaylistTrack", back_populates="track", cascade="all, delete-orphan")
    play_events = relationship("PlayEvent", back_populates="track", cascade="all, delete-orphan")
    implicit_ratings = relationship("ImplicitRating", back_populates="track", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="track", cascade="all, delete-orphan")
    similarities_as_track = relationship(
        "TrackSimilarity",
        foreign_keys="[TrackSimilarity.track_id]",
        back_populates="track",
        cascade="all, delete-orphan",
    )


class TrackGenre(Base):
    __tablename__ = "track_genres"

    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)

    track = relationship("Track", back_populates="genres")
    genre = relationship("Genre", back_populates="track_genres")
