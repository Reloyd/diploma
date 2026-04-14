#!/usr/bin/env python3
"""
Trigger audio feature extraction for all tracks that haven't been processed yet.
Sends tasks to the Celery ML worker via Redis.

Usage:
    python scripts/trigger_features.py
"""
import os
import sys
import urllib.parse

if sys.platform == "win32":
    os.environ.setdefault("PGPASSFILE", "NUL")
    os.environ.setdefault("PGSSLMODE", "disable")

import psycopg2
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_DB_URL = os.environ.get("DATABASE_SYNC_URL", "postgresql://phonoteka:phonoteka_pass@localhost:5432/phonoteka")

def _parse_db_url(url: str) -> dict:
    p = urllib.parse.urlparse(url)
    return {
        "host":     p.hostname or "localhost",
        "port":     p.port or 5432,
        "dbname":   (p.path or "/phonoteka").lstrip("/"),
        "user":     urllib.parse.unquote(p.username or "phonoteka"),
        "password": urllib.parse.unquote(p.password or "phonoteka_pass"),
        "options":  "-c client_encoding=UTF8",
    }

DB_PARAMS = _parse_db_url(_DB_URL)
app = Celery("phonoteka", broker=REDIS_URL)


def trigger_all():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM tracks WHERE features_extracted = false ORDER BY id")
    tracks = cur.fetchall()
    cur.close()
    conn.close()

    print(f"Queuing feature extraction for {len(tracks)} tracks...")
    for track_id, title in tracks:
        app.send_task("ml.extract_audio_features", args=[track_id], queue="ml")
        print(f"  Queued: [{track_id}] {title}")

    print(f"\nAll {len(tracks)} tasks queued. Monitor with:")
    print("  docker compose logs -f ml-worker")


if __name__ == "__main__":
    trigger_all()
