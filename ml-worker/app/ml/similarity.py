"""
Compute cosine similarity between tracks based on MFCC vectors.
Stores top-N similar tracks for each track in track_similarities table.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

# Inline model definitions to avoid circular imports
from sqlalchemy import Column, Integer, Float, String, JSON, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase

TOP_N = 20  # store top 20 similar tracks per track


class Base(DeclarativeBase):
    pass


def compute_and_store_similarities(db: Session, target_track_id: int, model_version: str = "v1"):
    """
    Compute cosine similarities between the target track and all other tracks
    with extracted MFCC vectors. Store top-N results.
    """
    from sqlalchemy import text

    # Load all features
    rows = db.execute(
        text("SELECT track_id, mfcc_vector FROM track_features WHERE mfcc_vector IS NOT NULL")
    ).fetchall()

    if len(rows) < 2:
        return  # not enough tracks

    track_ids = [r[0] for r in rows]
    vectors = np.array([r[1] for r in rows], dtype=np.float32)

    # Find index of target
    if target_track_id not in track_ids:
        return

    target_idx = track_ids.index(target_track_id)
    target_vec = vectors[target_idx].reshape(1, -1)

    # Cosine similarity between target and all others
    sims = cosine_similarity(target_vec, vectors)[0]  # shape: (N,)

    # Normalise to 0-1 (cosine is already -1 to 1, shift and scale)
    sims = (sims + 1.0) / 2.0

    # Get top-N excluding self
    sim_pairs = [(track_ids[i], float(sims[i])) for i in range(len(track_ids)) if track_ids[i] != target_track_id]
    sim_pairs.sort(key=lambda x: x[1], reverse=True)
    top_pairs = sim_pairs[:TOP_N]

    # Upsert into track_similarities
    db.execute(
        text("DELETE FROM track_similarities WHERE track_id = :tid"),
        {"tid": target_track_id},
    )
    for sim_track_id, score in top_pairs:
        db.execute(
            text("""
                INSERT INTO track_similarities (track_id, similar_track_id, similarity_score, model_version)
                VALUES (:tid, :sid, :score, :mv)
                ON CONFLICT (track_id, similar_track_id) DO UPDATE
                    SET similarity_score = EXCLUDED.similarity_score,
                        model_version = EXCLUDED.model_version
            """),
            {"tid": target_track_id, "sid": sim_track_id, "score": score, "mv": model_version},
        )
    db.commit()
