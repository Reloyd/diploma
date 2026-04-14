from sqlalchemy import Float, ForeignKey, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TrackFeature(Base):
    __tablename__ = "track_features"

    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    model_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)

    # Temporal features
    tempo: Mapped[float | None] = mapped_column(Float, nullable=True)          # BPM
    beat_strength: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1

    # Energy features
    rms_energy: Mapped[float | None] = mapped_column(Float, nullable=True)     # 0-1
    zero_crossing_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Spectral features
    spectral_centroid: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_rolloff: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_bandwidth: Mapped[float | None] = mapped_column(Float, nullable=True)

    # MFCC — stored as JSON array of 20 coefficients
    mfcc_vector: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Derived / normalised summary fields
    energy_level: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0-1 composite
    danceability: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0-1 composite
    valence: Mapped[float | None] = mapped_column(Float, nullable=True)        # 0-1 mood proxy

    track = relationship("Track", back_populates="features")


class TrackSimilarity(Base):
    __tablename__ = "track_similarities"

    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    similar_track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)     # 0-1 cosine similarity
    model_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)

    track = relationship("Track", foreign_keys=[track_id], back_populates="similarities_as_track")
    similar_track = relationship("Track", foreign_keys=[similar_track_id])
