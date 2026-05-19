"""
AI Assistant for playlist creation.
Calls Claude API (or returns mock) to extract structured parameters,
then queries DB using those parameters.
"""
import json
import random
from typing import Any
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.track import Track, TrackGenre, Genre
from app.models.track_features import TrackFeature
from app.models.playlist import Playlist, PlaylistTrack
from app.models.ratings import ImplicitRating


SYSTEM_PROMPT = """You are a music playlist assistant. Given a user request in any language,
extract structured parameters and return ONLY valid JSON.
Output format:
{
  "title": "string (short catchy playlist name, 2-5 words, in the user's language)",
  "context": "work|rest|sport|general",
  "genre": "string or null",
  "tempo_min": number_or_null,
  "tempo_max": number_or_null,
  "energy_min": number_or_null (0-1),
  "energy_max": number_or_null (0-1),
  "valence_min": number_or_null (0-1),
  "explanation": "string (1-2 sentences, human-readable, in the user's language)"
}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from model response, stripping markdown code blocks if present."""
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    # Find first { ... } block
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


async def _call_ai(prompt: str, context: str) -> dict:
    """Call AI API (Groq → Claude → mock) depending on available keys."""

    # --- Groq ---
    groq_key = getattr(settings, "GROQ_API_KEY", None)
    if groq_key and groq_key != "mock":
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"User request: {prompt}\nContext hint: {context}"},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            text = response.choices[0].message.content
            return _extract_json(text)
        except Exception as e:
            print(f"Groq API error: {e}")

    # --- Claude ---
    if settings.CLAUDE_API_KEY and settings.CLAUDE_API_KEY != "mock":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"User request: {prompt}\nContext hint: {context}"}],
            )
            text = response.content[0].text.strip()
            return _extract_json(text)
        except Exception as e:
            print(f"Claude API error: {e}")

    # --- Mock fallback ---
    return _mock_claude_response(prompt, context)


def _mock_claude_response(prompt: str, context: str) -> dict:
    """Generate a sensible mock response based on keywords."""
    prompt_lower = prompt.lower()

    # Detect context from keywords
    if any(w in prompt_lower for w in ["спорт", "бег", "трениров", "sport", "run", "workout", "gym"]):
        ctx = "sport"
        tempo_min, tempo_max = 120, 180
        energy_min, energy_max = 0.7, 1.0
    elif any(w in prompt_lower for w in ["работ", "учёб", "фокус", "work", "focus", "study", "concentration"]):
        ctx = "work"
        tempo_min, tempo_max = 70, 110
        energy_min, energy_max = 0.2, 0.6
    elif any(w in prompt_lower for w in ["отдых", "спокойн", "релакс", "rest", "relax", "chill", "calm"]):
        ctx = "rest"
        tempo_min, tempo_max = 60, 95
        energy_min, energy_max = 0.1, 0.4
    else:
        ctx = context
        tempo_min, tempo_max = None, None
        energy_min, energy_max = None, None

    # Detect genre keywords
    genre = None
    for kw, g in [("rock", "Rock"), ("jazz", "Jazz"), ("электрон", "Electronic"),
                  ("классик", "Classical"), ("pop", "Pop"), ("hip", "Hip-Hop"),
                  ("металл", "Metal"), ("инди", "Indie"), ("ambient", "Ambient")]:
        if kw in prompt_lower:
            genre = g
            break

    title_map = {
        "sport": "Энергия и драйв",
        "work": "Фокус и поток",
        "rest": "Спокойный вечер",
        "general": "Моя подборка",
    }
    return {
        "title": (genre + " микс") if genre else title_map.get(ctx, "Моя подборка"),
        "context": ctx,
        "genre": genre,
        "tempo_min": tempo_min,
        "tempo_max": tempo_max,
        "energy_min": energy_min,
        "energy_max": energy_max,
        "valence_min": None,
        "explanation": f"Подобрал треки по вашему запросу: «{prompt}». "
                       + (f"Жанр: {genre}. " if genre else "")
                       + "Приятного прослушивания!",
    }


async def _select_tracks(db: AsyncSession, user_id: int, params: dict, limit: int = 20) -> list[Track]:
    """Select tracks matching Claude-extracted parameters, ranked by implicit rating."""
    stmt = (
        select(Track)
        .options(
            selectinload(Track.artist),
            selectinload(Track.features),
            selectinload(Track.genres).selectinload(TrackGenre.genre),
        )
        .join(TrackFeature, Track.id == TrackFeature.track_id, isouter=True)
    )

    conditions = [Track.features_extracted.is_(True)]

    if params.get("genre"):
        stmt = stmt.join(TrackGenre, Track.id == TrackGenre.track_id).join(Genre)
        conditions.append(Genre.name.ilike(f"%{params['genre']}%"))

    if params.get("tempo_min") is not None:
        conditions.append(TrackFeature.tempo >= params["tempo_min"])
    if params.get("tempo_max") is not None:
        conditions.append(TrackFeature.tempo <= params["tempo_max"])
    if params.get("energy_min") is not None:
        conditions.append(TrackFeature.energy_level >= params["energy_min"])
    if params.get("energy_max") is not None:
        conditions.append(TrackFeature.energy_level <= params["energy_max"])
    if params.get("valence_min") is not None:
        conditions.append(TrackFeature.valence >= params["valence_min"])

    if len(conditions) > 1:
        stmt = stmt.where(and_(*conditions))

    # Try with strict filter first, fall back to loose if too few results
    tracks = (await db.execute(stmt.limit(limit * 3))).scalars().unique().all()

    if len(tracks) < 5:
        # Fall back: ignore audio feature filters, just filter by genre
        stmt2 = (
            select(Track)
            .options(selectinload(Track.artist), selectinload(Track.features))
        )
        if params.get("genre"):
            stmt2 = stmt2.join(TrackGenre).join(Genre).where(Genre.name.ilike(f"%{params['genre']}%"))
        tracks = (await db.execute(stmt2.limit(limit * 2))).scalars().unique().all()

    if not tracks:
        # Last resort: random tracks
        tracks = (await db.execute(
            select(Track).options(selectinload(Track.artist)).limit(limit * 2)
        )).scalars().unique().all()

    # Sort by implicit rating if available, then add diversity
    ratings = {}
    if tracks:
        track_ids = [t.id for t in tracks]
        rating_rows = (await db.execute(
            select(ImplicitRating).where(
                and_(ImplicitRating.user_id == user_id, ImplicitRating.track_id.in_(track_ids))
            )
        )).scalars().all()
        ratings = {r.track_id: r.score for r in rating_rows}

    # Score = implicit_rating * 0.4 + random jitter * 0.6
    # This ensures variety while still leaning toward liked tracks
    def diversity_score(t):
        base = ratings.get(t.id, 0.0)
        jitter = random.random()
        return base * 0.4 + jitter * 0.6

    ranked = sorted(tracks, key=diversity_score, reverse=True)
    return ranked[:limit]


async def create_ai_playlist(
    db: AsyncSession,
    user_id: int,
    prompt: str,
    context: str = "general",
) -> Playlist:
    """Full pipeline: prompt → Claude → params → tracks → Playlist."""
    params = await _call_ai(prompt, context)
    explanation = params.pop("explanation", "Плейлист создан ИИ-ассистентом.")
    resolved_context = params.pop("context", context)
    title = params.pop("title", None) or f"AI: {prompt[:40]}"

    tracks = await _select_tracks(db, user_id, params, limit=20)
    pl = Playlist(
        user_id=user_id,
        title=title,
        context=resolved_context,
        source="ai",
        ai_prompt=prompt,
        ai_explanation=explanation,
    )
    db.add(pl)
    await db.flush()

    for i, track in enumerate(tracks):
        db.add(PlaylistTrack(playlist_id=pl.id, track_id=track.id, position=i))

    await db.flush()

    # Reload with relationships
    pl_loaded = (await db.execute(
        select(Playlist)
        .options(
            selectinload(Playlist.tracks)
            .selectinload(PlaylistTrack.track)
            .selectinload(Track.artist),
        )
        .where(Playlist.id == pl.id)
    )).scalar_one()

    return pl_loaded
