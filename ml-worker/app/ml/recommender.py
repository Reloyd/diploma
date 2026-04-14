"""
Recommendation engine.

Combines:
  1. Implicit rating of tracks (user behaviour)
  2. User artist preferences
  3. User genre preferences
  4. Audio similarity (similar to highly-rated tracks)

For each recommendation stores:
  reason_type: similar_track | favorite_artist | favorite_genre | context
  reason_detail: human-readable explanation
"""
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

DECAY_DAYS = 30       # half-life for temporal decay
MAX_RECS = 50         # max recommendations stored per user


def _decay(last_event_at, now=None) -> float:
    """Exponential time decay: score * e^(-lambda * days_since)."""
    if last_event_at is None:
        return 1.0
    if now is None:
        now = datetime.now(timezone.utc)
    if last_event_at.tzinfo is None:
        last_event_at = last_event_at.replace(tzinfo=timezone.utc)
    days = (now - last_event_at).total_seconds() / 86400
    lam = math.log(2) / DECAY_DAYS
    return math.exp(-lam * days)


def build_recommendations(db: Session, user_id: int, context: str = "general"):
    """Compute and store recommendations for user."""
    now = datetime.now(timezone.utc)

    scores: dict[int, tuple[float, str, str]] = {}  # track_id -> (score, reason_type, reason_detail)

    # 1. Similar to highly-rated tracks
    rated = db.execute(
        text("""
            SELECT ir.track_id, ir.score, ir.last_event_at, t.title, a.name as artist_name
            FROM implicit_ratings ir
            JOIN tracks t ON t.id = ir.track_id
            JOIN artists a ON a.id = t.artist_id
            WHERE ir.user_id = :uid AND ir.score > 0.3
            ORDER BY ir.score DESC LIMIT 10
        """),
        {"uid": user_id},
    ).fetchall()

    for row in rated:
        decay = _decay(row.last_event_at, now)
        base_score = row.score * decay

        # Find similar tracks
        sims = db.execute(
            text("""
                SELECT ts.similar_track_id, ts.similarity_score
                FROM track_similarities ts
                WHERE ts.track_id = :tid
                ORDER BY ts.similarity_score DESC LIMIT 10
            """),
            {"tid": row.track_id},
        ).fetchall()

        for sim in sims:
            sim_id = sim.similar_track_id
            contrib = base_score * sim.similarity_score * 0.7
            if sim_id not in scores or scores[sim_id][0] < contrib:
                scores[sim_id] = (
                    contrib,
                    "similar_track",
                    f"Похоже на «{row.title}» — {row.artist_name}",
                )

    # 2. Favourite artists
    fav_artists = db.execute(
        text("""
            SELECT uap.artist_id, uap.score, a.name
            FROM user_artist_preferences uap
            JOIN artists a ON a.id = uap.artist_id
            WHERE uap.user_id = :uid AND uap.score > 0.2
            ORDER BY uap.score DESC LIMIT 5
        """),
        {"uid": user_id},
    ).fetchall()

    for fav in fav_artists:
        tracks_by_artist = db.execute(
            text("SELECT id, title FROM tracks WHERE artist_id = :aid LIMIT 20"),
            {"aid": fav.artist_id},
        ).fetchall()
        for t in tracks_by_artist:
            contrib = fav.score * 0.6
            if t.id not in scores or scores[t.id][0] < contrib:
                scores[t.id] = (contrib, "favorite_artist", f"Исполнитель: {fav.name}")

    # 3. Favourite genres
    fav_genres = db.execute(
        text("""
            SELECT ugp.genre_id, ugp.score, g.name
            FROM user_genre_preferences ugp
            JOIN genres g ON g.id = ugp.genre_id
            WHERE ugp.user_id = :uid AND ugp.score > 0.2
            ORDER BY ugp.score DESC LIMIT 5
        """),
        {"uid": user_id},
    ).fetchall()

    for fav in fav_genres:
        tracks_in_genre = db.execute(
            text("""
                SELECT t.id FROM tracks t
                JOIN track_genres tg ON tg.track_id = t.id
                WHERE tg.genre_id = :gid LIMIT 20
            """),
            {"gid": fav.genre_id},
        ).fetchall()
        for t in tracks_in_genre:
            contrib = fav.score * 0.5
            if t.id not in scores or scores[t.id][0] < contrib:
                scores[t.id] = (contrib, "favorite_genre", f"Жанр: {fav.name}")

    # 4. Context-based (if context != general, filter by audio features)
    if context != "general":
        context_ranges = {
            "sport": {"tempo_min": 120, "energy_min": 0.6},
            "work":  {"tempo_max": 110, "energy_max": 0.6},
            "rest":  {"tempo_max": 95,  "energy_max": 0.4},
        }
        cond = context_ranges.get(context, {})
        filters = []
        params: dict = {}
        if "tempo_min" in cond:
            filters.append("tf.tempo >= :tempo_min")
            params["tempo_min"] = cond["tempo_min"]
        if "tempo_max" in cond:
            filters.append("tf.tempo <= :tempo_max")
            params["tempo_max"] = cond["tempo_max"]
        if "energy_min" in cond:
            filters.append("tf.energy_level >= :energy_min")
            params["energy_min"] = cond["energy_min"]
        if "energy_max" in cond:
            filters.append("tf.energy_level <= :energy_max")
            params["energy_max"] = cond["energy_max"]

        if filters:
            where = " AND ".join(filters)
            ctx_tracks = db.execute(
                text(f"SELECT t.id FROM tracks t JOIN track_features tf ON tf.track_id = t.id WHERE {where} LIMIT 30"),
                params,
            ).fetchall()
            for t in ctx_tracks:
                contrib = 0.4
                if t.id not in scores or scores[t.id][0] < contrib:
                    scores[t.id] = (contrib, "context", f"Подходит для: {context}")

    # If no scores yet (new user), use random tracks
    if not scores:
        random_tracks = db.execute(
            text("SELECT id FROM tracks ORDER BY RANDOM() LIMIT 30")
        ).fetchall()
        for t in random_tracks:
            scores[t.id] = (0.1, "context", "Новинки каталога")

    # Remove already-liked tracks (score >= 0.8)
    high_rated = db.execute(
        text("SELECT track_id FROM implicit_ratings WHERE user_id = :uid AND score >= 0.8"),
        {"uid": user_id},
    ).fetchall()
    for t in high_rated:
        scores.pop(t.track_id, None)

    # Sort and take top-MAX_RECS
    sorted_recs = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)[:MAX_RECS]

    # Store
    db.execute(
        text("DELETE FROM recommendations WHERE user_id = :uid AND context = :ctx"),
        {"uid": user_id, "ctx": context},
    )
    for track_id, (score, reason_type, reason_detail) in sorted_recs:
        db.execute(
            text("""
                INSERT INTO recommendations (user_id, track_id, score, reason_type, reason_detail, context)
                VALUES (:uid, :tid, :score, :rt, :rd, :ctx)
            """),
            {"uid": user_id, "tid": track_id, "score": score,
             "rt": reason_type, "rd": reason_detail, "ctx": context},
        )
    db.commit()
