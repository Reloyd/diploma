#!/usr/bin/env python3
"""
Seed database with demo data (no Jamendo API key required).
Uses public domain / CC0 tracks from Free Music Archive links.
For development and testing only.

Usage:
    python scripts/seed_demo.py
"""
import os
import sys
import urllib.parse

if sys.platform == "win32":
    os.environ.setdefault("PGPASSFILE", "NUL")
    os.environ.setdefault("PGSSLMODE", "disable")

import psycopg2
import json

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

# Demo tracks using public Jamendo stream URLs (no auth needed for CC tracks)
DEMO_DATA = [
    {
        "artist": "Jahzzar", "genre": "Electronic",
        "tracks": [
            {"title": "Trellis", "url": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Jahzzar/Traveller/Jahzzar_-_01_-_Trellis.mp3", "duration": 185},
        ]
    },
    {
        "artist": "Kevin MacLeod", "genre": "Ambient",
        "tracks": [
            {"title": "Cipher", "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cipher.mp3", "duration": 170},
            {"title": "Impact Allegretto", "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Impact%20Allegretto.mp3", "duration": 140},
            {"title": "Relaxing Piano Music", "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Relaxing%20Piano%20Music.mp3", "duration": 200},
        ]
    },
    {
        "artist": "Lee Rosevere", "genre": "Ambient",
        "tracks": [
            {"title": "Music For Podcasts 5", "url": "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/WFMU/Lee_Rosevere/Music_For_Podcasts_5/Lee_Rosevere_-_01_-_Lets_Start_at_the_Beginning.mp3", "duration": 150},
        ]
    },
]

GENRES = ["Electronic", "Ambient", "Rock", "Jazz", "Pop", "Hip-Hop", "Classical", "Indie", "Folk", "Metal"]


def seed():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = False
    cur = conn.cursor()

    # Insert genres
    for genre in GENRES:
        cur.execute("INSERT INTO genres (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (genre,))

    # Insert demo tracks
    for item in DEMO_DATA:
        cur.execute("""
            INSERT INTO artists (name) VALUES (%s)
            ON CONFLICT DO NOTHING RETURNING id
        """, (item["artist"],))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT id FROM artists WHERE name = %s", (item["artist"],))
            row = cur.fetchone()
        artist_id = row[0]

        cur.execute("SELECT id FROM genres WHERE name = %s", (item["genre"],))
        genre_id = cur.fetchone()[0]

        for t in item["tracks"]:
            cur.execute("""
                INSERT INTO tracks (title, artist_id, duration_sec, file_url, features_extracted)
                VALUES (%s, %s, %s, %s, false)
                ON CONFLICT DO NOTHING RETURNING id
            """, (t["title"], artist_id, t["duration"], t["url"]))
            row = cur.fetchone()
            if row:
                track_id = row[0]
                cur.execute("INSERT INTO track_genres (track_id, genre_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (track_id, genre_id))

    conn.commit()
    cur.close()
    conn.close()
    print("Demo data seeded successfully!")
    print("You can now start the app with: docker compose up")


if __name__ == "__main__":
    seed()
