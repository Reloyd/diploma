"""
Celery worker — ML tasks.
Task names match the stubs in backend/app/tasks.py.
"""
import json
import os
import tempfile
import urllib.request

from celery import Celery
from app.config import settings

celery_app = Celery(
    "phonoteka_ml",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.task_routes = {"ml.*": {"queue": "ml"}}
celery_app.conf.worker_prefetch_multiplier = 1


def _download_audio(file_url: str, dest_path: str) -> bool:
    """Download audio from URL (MinIO presigned or public) to local path."""
    try:
        if file_url.startswith("minio://"):
            # Internal MinIO path: minio://bucket/object
            _, rest = file_url.split("://", 1)
            bucket, obj = rest.split("/", 1)
            from minio import Minio
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            client.fget_object(bucket, obj, dest_path)
        else:
            urllib.request.urlretrieve(file_url, dest_path)
        return True
    except Exception as e:
        print(f"Download failed for {file_url}: {e}")
        return False


@celery_app.task(name="ml.extract_audio_features")
def extract_audio_features(track_id: int):
    """Extract audio features for a track and update DB."""
    from app.database import SessionLocal
    from sqlalchemy import text
    from app.ml.feature_extractor import extract_features
    from app.ml.similarity import compute_and_store_similarities

    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT id, file_url FROM tracks WHERE id = :tid"),
            {"tid": track_id},
        ).fetchone()

        if not row:
            print(f"Track {track_id} not found")
            return

        os.makedirs(settings.AUDIO_TMP_DIR, exist_ok=True)
        tmp_path = os.path.join(settings.AUDIO_TMP_DIR, f"track_{track_id}.mp3")

        if not _download_audio(row.file_url, tmp_path):
            return

        features = extract_features(tmp_path)

        # Clean up temp file
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        if features is None:
            return

        db.execute(
            text("""
                INSERT INTO track_features
                    (track_id, model_version, tempo, beat_strength, rms_energy, zero_crossing_rate,
                     spectral_centroid, spectral_rolloff, spectral_bandwidth, mfcc_vector,
                     energy_level, danceability, valence)
                VALUES
                    (:tid, :mv, :tempo, :bs, :rms, :zcr,
                     :sc, :sr, :sb, :mfcc,
                     :el, :dance, :valence)
                ON CONFLICT (track_id) DO UPDATE SET
                    model_version = EXCLUDED.model_version,
                    tempo = EXCLUDED.tempo,
                    beat_strength = EXCLUDED.beat_strength,
                    rms_energy = EXCLUDED.rms_energy,
                    zero_crossing_rate = EXCLUDED.zero_crossing_rate,
                    spectral_centroid = EXCLUDED.spectral_centroid,
                    spectral_rolloff = EXCLUDED.spectral_rolloff,
                    spectral_bandwidth = EXCLUDED.spectral_bandwidth,
                    mfcc_vector = EXCLUDED.mfcc_vector,
                    energy_level = EXCLUDED.energy_level,
                    danceability = EXCLUDED.danceability,
                    valence = EXCLUDED.valence
            """),
            {
                "tid": track_id, "mv": settings.ML_MODEL_VERSION,
                "tempo": features.tempo, "bs": features.beat_strength,
                "rms": features.rms_energy, "zcr": features.zero_crossing_rate,
                "sc": features.spectral_centroid, "sr": features.spectral_rolloff,
                "sb": features.spectral_bandwidth, "mfcc": json.dumps(features.mfcc_vector),
                "el": features.energy_level, "dance": features.danceability,
                "valence": features.valence,
            },
        )
        db.execute(
            text("UPDATE tracks SET features_extracted = true WHERE id = :tid"),
            {"tid": track_id},
        )
        db.commit()

        # Compute similarity against other tracks
        compute_and_store_similarities(db, track_id, settings.ML_MODEL_VERSION)

        print(f"Features extracted for track {track_id}: tempo={features.tempo:.1f}")

    except Exception as e:
        print(f"extract_audio_features error for track {track_id}: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="ml.recalculate_ratings")
def recalculate_ratings(user_id: int, track_id: int):
    """Recalculate implicit rating after a play event."""
    from app.database import SessionLocal
    from app.ml.ratings import recalculate_rating

    db = SessionLocal()
    try:
        recalculate_rating(db, user_id, track_id)
        # Rebuild recommendations for this user after rating update
        rebuild_recommendations.delay(user_id, "general")
    except Exception as e:
        print(f"recalculate_ratings error: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="ml.build_recommendations")
def rebuild_recommendations(user_id: int, context: str = "general"):
    """Build personalized recommendations for user."""
    from app.database import SessionLocal
    from app.ml.recommender import build_recommendations

    db = SessionLocal()
    try:
        build_recommendations(db, user_id, context)
        print(f"Recommendations rebuilt for user {user_id}, context={context}")
    except Exception as e:
        print(f"rebuild_recommendations error: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="ml.compute_similarities")
def compute_similarities(track_id: int):
    """Compute/recompute similarities for a given track."""
    from app.database import SessionLocal
    from app.ml.similarity import compute_and_store_similarities

    db = SessionLocal()
    try:
        compute_and_store_similarities(db, track_id)
    except Exception as e:
        print(f"compute_similarities error: {e}")
        db.rollback()
    finally:
        db.close()
