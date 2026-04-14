#!/usr/bin/env python3
"""
Dataset loader for Phonoteka.
Loads tracks from Jamendo API (Creative Commons) into PostgreSQL + MinIO.

Usage:
    python scripts/load_dataset.py --limit 200 --client-id YOUR_JAMENDO_CLIENT_ID

Get a free Jamendo API client ID at: https://developer.jamendo.com/v3.0
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── Windows Cyrillic-path fix ────────────────────────────────────────────────
# psycopg2 tries to read %APPDATA%\postgresql\pgpass.conf even when explicit
# connection params are given. On Windows with a Cyrillic username the path
# is encoded as Windows-1251, causing UnicodeDecodeError.
# Setting PGPASSFILE=NUL (Windows null device) prevents the lookup entirely.
if sys.platform == "win32":
    os.environ.setdefault("PGPASSFILE", "NUL")
    os.environ.setdefault("PGSSLMODE", "disable")
# ─────────────────────────────────────────────────────────────────────────────

import psycopg2
from minio import Minio
from minio.error import S3Error
import io

# --- Config from env ---
_DB_URL = os.environ.get(
    "DATABASE_SYNC_URL",
    "postgresql://phonoteka:phonoteka_pass@localhost:5432/phonoteka"
)

def _parse_db_url(url: str) -> dict:
    """Parse postgres:// URL into psycopg2 kwargs (avoids URL-level encoding issues)."""
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

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET_AUDIO = os.environ.get("MINIO_BUCKET_AUDIO", "audio")
MINIO_BUCKET_COVERS = os.environ.get("MINIO_BUCKET_COVERS", "covers")

JAMENDO_API = "https://api.jamendo.com/v3.0"


def fetch_jamendo_tracks(client_id: str, limit: int = 200, offset: int = 0) -> list[dict]:
    """Fetch Creative Commons tracks from Jamendo API."""
    url = (
        f"{JAMENDO_API}/tracks/"
        f"?client_id={client_id}"
        f"&format=json"
        f"&limit={min(limit, 200)}"
        f"&offset={offset}"
        f"&include=musicinfo"
        f"&audioformat=mp32"
        f"&imagesize=200"
        f"&order=popularity_total"
        f"&ccsa=1"  # share-alike CC licenses
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("results", [])
    except Exception as e:
        print(f"Jamendo API error: {e}")
        return []


def ensure_minio_buckets(client: Minio):
    for bucket in [MINIO_BUCKET_AUDIO, MINIO_BUCKET_COVERS]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"Created MinIO bucket: {bucket}")


def upload_to_minio(client: Minio, bucket: str, object_name: str, url: str,
                    content_type: str = "audio/mpeg") -> str | None:
    """Download from URL and upload to MinIO. Returns minio:// path or None."""
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
        client.put_object(bucket, object_name, io.BytesIO(data), len(data), content_type=content_type)
        return f"minio://{bucket}/{object_name}"
    except Exception as e:
        print(f"  Upload failed ({url[:60]}): {e}")
        return None


def load_tracks(client_id: str, limit: int = 200, upload_audio: bool = True, dry_run: bool = False):
    print(f"Loading up to {limit} tracks from Jamendo...")

    minio = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    ensure_minio_buckets(minio)

    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = False
    cur = conn.cursor()

    loaded = 0
    offset = 0
    batch_size = 50

    while loaded < limit:
        tracks = fetch_jamendo_tracks(client_id, min(batch_size, limit - loaded), offset)
        if not tracks:
            break

        for t in tracks:
            try:
                name = t.get("artist_name", "Unknown Artist")
                jamendo_artist_id = str(t.get("artist_id", ""))

                # Upsert artist
                cur.execute("""
                    INSERT INTO artists (name, jamendo_id)
                    VALUES (%s, %s)
                    ON CONFLICT (jamendo_id) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, (name, jamendo_artist_id))
                artist_id = cur.fetchone()[0]

                # Upsert album
                album_name = t.get("album_name") or t.get("name", "Single")
                jamendo_album_id = str(t.get("album_id", "")) or None
                cover_url_orig = t.get("image", "")
                cover_url = cover_url_orig  # use original URL for covers

                if jamendo_album_id:
                    cur.execute("""
                        INSERT INTO albums (title, artist_id, cover_url, jamendo_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (jamendo_id) DO UPDATE SET title = EXCLUDED.title
                        RETURNING id
                    """, (album_name, artist_id, cover_url, jamendo_album_id))
                    album_id = cur.fetchone()[0]
                else:
                    album_id = None

                # Audio file
                jamendo_track_id = str(t.get("id", ""))
                audio_url_orig = t.get("audio", "")

                if upload_audio and audio_url_orig and not dry_run:
                    object_name = f"jamendo_{jamendo_track_id}.mp3"
                    file_url = upload_to_minio(minio, MINIO_BUCKET_AUDIO, object_name, audio_url_orig)
                    if not file_url:
                        file_url = audio_url_orig  # fallback to original URL
                else:
                    file_url = audio_url_orig  # use Jamendo direct URL

                # Upsert track
                duration = float(t.get("duration", 0))
                cur.execute("""
                    INSERT INTO tracks (title, artist_id, album_id, duration_sec, file_url, cover_url, license_type, jamendo_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (jamendo_id) DO UPDATE SET
                        file_url = EXCLUDED.file_url,
                        cover_url = EXCLUDED.cover_url
                    RETURNING id
                """, (
                    t.get("name", "Unknown"),
                    artist_id, album_id, duration,
                    file_url, cover_url,
                    t.get("license_ccurl", "CC"),
                    jamendo_track_id,
                ))
                track_id = cur.fetchone()[0]

                # Genres
                music_info = t.get("musicinfo", {})
                tags = music_info.get("tags", {})
                genres_list = tags.get("genres", []) or []
                vartags = tags.get("vartags", []) or []

                all_genres = list(set(genres_list + vartags))[:5]
                for genre_name in all_genres:
                    if not genre_name:
                        continue
                    cur.execute("""
                        INSERT INTO genres (name) VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                        RETURNING id
                    """, (genre_name.capitalize(),))
                    row = cur.fetchone()
                    if row:
                        genre_id = row[0]
                    else:
                        cur.execute("SELECT id FROM genres WHERE name = %s", (genre_name.capitalize(),))
                        genre_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO track_genres (track_id, genre_id)
                        VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """, (track_id, genre_id))

                loaded += 1
                print(f"  [{loaded}/{limit}] {t.get('name')} — {name}")

                # Commit every 10 tracks
                if loaded % 10 == 0:
                    conn.commit()

            except Exception as e:
                print(f"  Error loading track {t.get('id')}: {e}")
                conn.rollback()
                continue

        conn.commit()
        offset += batch_size
        time.sleep(0.5)  # be nice to Jamendo API

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone! Loaded {loaded} tracks.")
    print("Now queue audio feature extraction by running:")
    print("  python scripts/trigger_features.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Jamendo dataset")
    parser.add_argument("--client-id", required=True, help="Jamendo API client ID")
    parser.add_argument("--limit", type=int, default=200, help="Number of tracks to load")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload audio to MinIO (use Jamendo URLs directly)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual uploads)")
    args = parser.parse_args()

    load_tracks(
        client_id=args.client_id,
        limit=args.limit,
        upload_audio=not args.no_upload,
        dry_run=args.dry_run,
    )
