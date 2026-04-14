"""Celery task stubs — the real implementations live in ml-worker."""
from celery import Celery
from app.config import settings

celery_app = Celery("phonoteka", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {
    "ml.*": {"queue": "ml"},
}

# These are send-only task references (no implementation here —
# they are implemented in ml-worker and registered under the same names)

@celery_app.task(name="ml.extract_audio_features")
def extract_audio_features_task(track_id: int):
    pass


@celery_app.task(name="ml.recalculate_ratings")
def recalculate_ratings_task(user_id: int, track_id: int):
    pass


@celery_app.task(name="ml.build_recommendations")
def build_recommendations_task(user_id: int, context: str = "general"):
    pass


@celery_app.task(name="ml.compute_similarities")
def compute_similarities_task(track_id: int):
    pass
