from pydantic import BaseModel
from datetime import datetime


class GenreOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ArtistOut(BaseModel):
    id: int
    name: str
    bio: str | None = None
    image_url: str | None = None

    model_config = {"from_attributes": True}


class AlbumOut(BaseModel):
    id: int
    title: str
    artist_id: int
    cover_url: str | None = None
    release_year: int | None = None

    model_config = {"from_attributes": True}


class TrackFeatureOut(BaseModel):
    tempo: float | None = None
    beat_strength: float | None = None
    rms_energy: float | None = None
    spectral_centroid: float | None = None
    energy_level: float | None = None
    danceability: float | None = None
    valence: float | None = None

    model_config = {"from_attributes": True}


class TrackBrief(BaseModel):
    id: int
    title: str
    artist_id: int
    artist_name: str = ""
    cover_url: str | None = None
    duration_sec: float | None = None
    file_url: str

    model_config = {"from_attributes": True}


class TrackOut(BaseModel):
    id: int
    title: str
    artist: ArtistOut
    album: AlbumOut | None = None
    genres: list[GenreOut] = []
    duration_sec: float | None = None
    file_url: str
    cover_url: str | None = None
    features: TrackFeatureOut | None = None
    in_library: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
