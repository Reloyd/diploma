"""
Implicit rating computation.

Formula:
  base = (play_count_score * 0.4) + (avg_played_ratio * 0.3) + (like_bonus * 0.2) - (skip_penalty * 0.1)
  score = clip(base, 0, 1)

Where:
  play_count_score = min(play_count / 10, 1.0)   # saturates at 10 plays
  like_bonus = 1.0 if liked else 0.0
  skip_penalty = min(skip_count / play_count, 1.0) if play_count > 0 else 0.0
"""
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text


def recalculate_rating(db: Session, user_id: int, track_id: int):
    """Recalculate and upsert implicit rating for user-track pair."""

    row = db.execute(
        text("""
            SELECT
                COUNT(*) as play_count,
                AVG(played_ratio) as avg_played_ratio,
                SUM(CASE WHEN skipped THEN 1 ELSE 0 END) as skip_count,
                BOOL_OR(liked) as liked,
                MAX(occurred_at) as last_event_at
            FROM play_events
            WHERE user_id = :uid AND track_id = :tid
        """),
        {"uid": user_id, "tid": track_id},
    ).fetchone()

    if row is None or row.play_count == 0:
        return

    play_count = int(row.play_count)
    avg_played_ratio = float(row.avg_played_ratio or 0.0)
    skip_count = int(row.skip_count or 0)
    liked = bool(row.liked or False)
    last_event_at = row.last_event_at

    play_count_score = min(play_count / 10.0, 1.0)
    skip_penalty = min(skip_count / play_count, 1.0) if play_count > 0 else 0.0
    like_bonus = 1.0 if liked else 0.0

    base = (play_count_score * 0.4) + (avg_played_ratio * 0.3) + (like_bonus * 0.2) - (skip_penalty * 0.1)
    score = max(0.0, min(1.0, base))

    db.execute(
        text("""
            INSERT INTO implicit_ratings
                (user_id, track_id, score, play_count, avg_played_ratio, skip_count, liked, last_event_at, updated_at)
            VALUES
                (:uid, :tid, :score, :pc, :apr, :sc, :liked, :lea, now())
            ON CONFLICT (user_id, track_id) DO UPDATE SET
                score = EXCLUDED.score,
                play_count = EXCLUDED.play_count,
                avg_played_ratio = EXCLUDED.avg_played_ratio,
                skip_count = EXCLUDED.skip_count,
                liked = EXCLUDED.liked,
                last_event_at = EXCLUDED.last_event_at,
                updated_at = now()
        """),
        {"uid": user_id, "tid": track_id, "score": score,
         "pc": play_count, "apr": avg_played_ratio, "sc": skip_count,
         "liked": liked, "lea": last_event_at},
    )

    # Update artist preference
    artist_row = db.execute(
        text("SELECT artist_id FROM tracks WHERE id = :tid"),
        {"tid": track_id},
    ).fetchone()
    if artist_row:
        db.execute(
            text("""
                INSERT INTO user_artist_preferences (user_id, artist_id, score, updated_at)
                VALUES (:uid, :aid, :score, now())
                ON CONFLICT (user_id, artist_id) DO UPDATE SET
                    score = (user_artist_preferences.score * 0.7) + (EXCLUDED.score * 0.3),
                    updated_at = now()
            """),
            {"uid": user_id, "aid": artist_row.artist_id, "score": score},
        )

    # Update genre preferences
    genres = db.execute(
        text("SELECT genre_id FROM track_genres WHERE track_id = :tid"),
        {"tid": track_id},
    ).fetchall()
    for g in genres:
        db.execute(
            text("""
                INSERT INTO user_genre_preferences (user_id, genre_id, score, updated_at)
                VALUES (:uid, :gid, :score, now())
                ON CONFLICT (user_id, genre_id) DO UPDATE SET
                    score = (user_genre_preferences.score * 0.7) + (EXCLUDED.score * 0.3),
                    updated_at = now()
            """),
            {"uid": user_id, "gid": g.genre_id, "score": score},
        )

    db.commit()
