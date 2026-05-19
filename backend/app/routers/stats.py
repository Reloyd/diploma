from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import zoneinfo
from datetime import date, timedelta, datetime

from app.database import get_db
from app.models.user import User
from app.services.deps import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(
    tz: str = Query("UTC"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id

    # Validate timezone to prevent injection
    try:
        zoneinfo.ZoneInfo(tz)
    except Exception:
        tz = "UTC"

    # --- Summary ---
    summary_row = (await db.execute(text("""
        SELECT
            COALESCE(SUM(played_seconds), 0)            AS total_seconds,
            COUNT(*)                                     AS total_plays,
            COUNT(DISTINCT track_id)                     AS unique_tracks,
            COALESCE(AVG(played_ratio), 0)               AS avg_completion,
            COALESCE(
                SUM(CASE WHEN skipped THEN 1 ELSE 0 END)::float
                / NULLIF(COUNT(*), 0), 0
            )                                            AS skip_rate
        FROM play_events
        WHERE user_id = :uid
    """), {"uid": uid})).fetchone()

    # Listening days streak (consecutive days with at least 1 play)
    streak_row = (await db.execute(text("""
        WITH daily AS (
            SELECT DISTINCT DATE(occurred_at AT TIME ZONE :tz) AS d FROM play_events WHERE user_id = :uid
        ),
        gaps AS (
            SELECT d, d - LAG(d) OVER (ORDER BY d) AS gap FROM daily
        ),
        groups AS (
            SELECT d, SUM(CASE WHEN gap > 1 OR gap IS NULL THEN 1 ELSE 0 END)
                OVER (ORDER BY d) AS grp FROM gaps
        )
        SELECT COUNT(*) AS streak FROM groups
        WHERE grp = (SELECT grp FROM groups ORDER BY d DESC LIMIT 1)
    """), {"uid": uid, "tz": tz})).fetchone()

    # --- Activity last 30 days ---
    activity_rows = (await db.execute(text("""
        SELECT
            DATE(occurred_at AT TIME ZONE :tz)              AS day,
            COUNT(*)                                         AS plays,
            COALESCE(SUM(played_seconds) / 60.0, 0)         AS minutes
        FROM play_events
        WHERE user_id = :uid
          AND occurred_at >= NOW() - INTERVAL '31 days'
        GROUP BY DATE(occurred_at AT TIME ZONE :tz)
        ORDER BY day
    """), {"uid": uid, "tz": tz})).fetchall()

    # Fill missing days with 0
    user_tz = zoneinfo.ZoneInfo(tz)
    activity_map = {str(r.day): {"plays": r.plays, "minutes": round(float(r.minutes), 1)}
                    for r in activity_rows}
    activity = []
    today = datetime.now(user_tz).date()
    for i in range(29, -1, -1):
        d = str(today - timedelta(days=i))
        activity.append({
            "date": d,
            "plays": activity_map.get(d, {}).get("plays", 0),
            "minutes": activity_map.get(d, {}).get("minutes", 0.0),
        })

    # --- Top tracks ---
    top_tracks = (await db.execute(text("""
        SELECT
            t.id, t.title, t.cover_url, t.duration_sec,
            a.name AS artist_name,
            ir.play_count,
            ir.score,
            ir.avg_played_ratio
        FROM implicit_ratings ir
        JOIN tracks t ON t.id = ir.track_id
        LEFT JOIN artists a ON a.id = t.artist_id
        WHERE ir.user_id = :uid
        ORDER BY ir.play_count DESC, ir.score DESC
        LIMIT 10
    """), {"uid": uid})).fetchall()

    # --- Top artists ---
    top_artists = (await db.execute(text("""
        SELECT a.id, a.name, a.image_url, uap.score,
               COUNT(DISTINCT t.id) AS track_count
        FROM user_artist_preferences uap
        JOIN artists a ON a.id = uap.artist_id
        LEFT JOIN tracks t ON t.artist_id = a.id
        WHERE uap.user_id = :uid
        GROUP BY a.id, a.name, a.image_url, uap.score
        ORDER BY uap.score DESC
        LIMIT 8
    """), {"uid": uid})).fetchall()

    # --- Top genres ---
    top_genres = (await db.execute(text("""
        SELECT g.name, ugp.score
        FROM user_genre_preferences ugp
        JOIN genres g ON g.id = ugp.genre_id
        WHERE ugp.user_id = :uid
        ORDER BY ugp.score DESC
        LIMIT 8
    """), {"uid": uid})).fetchall()

    # --- Listening by hour of day ---
    by_hour = (await db.execute(text("""
        SELECT EXTRACT(HOUR FROM occurred_at AT TIME ZONE :tz)::int AS hour, COUNT(*) AS plays
        FROM play_events
        WHERE user_id = :uid
        GROUP BY hour
        ORDER BY hour
    """), {"uid": uid, "tz": tz})).fetchall()
    hour_map = {r.hour: r.plays for r in by_hour}
    by_hour_full = [{"hour": h, "plays": hour_map.get(h, 0)} for h in range(24)]

    total_seconds = float(summary_row.total_seconds or 0)
    total_hours = round(total_seconds / 3600, 1)
    total_minutes = round(total_seconds / 60, 0)

    return {
        "summary": {
            "total_hours": total_hours,
            "total_minutes": int(total_minutes),
            "total_plays": summary_row.total_plays or 0,
            "unique_tracks": summary_row.unique_tracks or 0,
            "avg_completion": round(float(summary_row.avg_completion or 0) * 100, 1),
            "skip_rate": round(float(summary_row.skip_rate or 0) * 100, 1),
            "streak_days": streak_row.streak if streak_row else 0,
        },
        "activity": activity,
        "top_tracks": [
            {
                "id": r.id,
                "title": r.title,
                "artist_name": r.artist_name or "",
                "cover_url": r.cover_url,
                "play_count": r.play_count,
                "score": round(float(r.score), 2),
                "avg_completion": round(float(r.avg_played_ratio or 0) * 100, 1),
            }
            for r in top_tracks
        ],
        "top_artists": [
            {
                "id": r.id,
                "name": r.name,
                "image_url": r.image_url,
                "score": round(float(r.score), 2),
                "track_count": r.track_count,
            }
            for r in top_artists
        ],
        "top_genres": [
            {"name": r.name, "score": round(float(r.score), 2)}
            for r in top_genres
        ],
        "by_hour": by_hour_full,
    }
