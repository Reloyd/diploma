"""
Audio feature extraction pipeline using librosa.
Extracts: tempo, beat_strength, rms_energy, zero_crossing_rate,
spectral_centroid, spectral_rolloff, spectral_bandwidth, mfcc_vector (20 coefficients).
Also computes derived features: energy_level, danceability, valence.
"""
import os
import tempfile
from dataclasses import dataclass
from typing import Optional

import numpy as np
import librosa


@dataclass
class AudioFeatures:
    tempo: float
    beat_strength: float
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid: float
    spectral_rolloff: float
    spectral_bandwidth: float
    mfcc_vector: list[float]  # 20 coefficients
    energy_level: float       # 0-1 composite
    danceability: float       # 0-1 composite
    valence: float            # 0-1 mood proxy


def extract_features(audio_path: str) -> Optional[AudioFeatures]:
    """
    Load audio file and extract all features.
    Returns None if extraction fails.
    """
    try:
        # Load with target sample rate 22050 Hz, mono, max 60 seconds for efficiency
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=60.0)

        # --- Temporal ---
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo)

        # Beat strength: mean strength of beat frames
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        beat_strength = float(np.mean(onset_env[beat_frames])) if len(beat_frames) > 0 else 0.0
        # Normalize beat_strength to 0-1 using sigmoid-like clip
        beat_strength = float(np.clip(beat_strength / 10.0, 0.0, 1.0))

        # --- Energy ---
        rms = librosa.feature.rms(y=y)[0]
        rms_energy = float(np.mean(rms))
        rms_energy = float(np.clip(rms_energy * 10.0, 0.0, 1.0))  # normalise

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zero_crossing_rate = float(np.mean(zcr))

        # --- Spectral ---
        spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))
        spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0]))
        spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]))

        # --- MFCC (20 coefficients, mean over time) ---
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        mfcc_vector = [float(v) for v in np.mean(mfcc, axis=1)]

        # --- Derived features ---
        # energy_level: combination of RMS + spectral centroid (brighter = more energetic)
        norm_centroid = float(np.clip(spectral_centroid / (sr / 2), 0.0, 1.0))
        energy_level = float(np.clip((rms_energy * 0.6 + norm_centroid * 0.4), 0.0, 1.0))

        # danceability: how well the beat is defined relative to energy
        danceability = float(np.clip((beat_strength * 0.7 + rms_energy * 0.3), 0.0, 1.0))

        # valence (mood proxy): high ZCR + high spectral centroid → brighter/happier
        norm_zcr = float(np.clip(zero_crossing_rate * 20.0, 0.0, 1.0))
        valence = float(np.clip((norm_centroid * 0.5 + norm_zcr * 0.5), 0.0, 1.0))

        return AudioFeatures(
            tempo=tempo,
            beat_strength=beat_strength,
            rms_energy=rms_energy,
            zero_crossing_rate=zero_crossing_rate,
            spectral_centroid=spectral_centroid,
            spectral_rolloff=spectral_rolloff,
            spectral_bandwidth=spectral_bandwidth,
            mfcc_vector=mfcc_vector,
            energy_level=energy_level,
            danceability=danceability,
            valence=valence,
        )

    except Exception as e:
        print(f"Feature extraction failed for {audio_path}: {e}")
        return None
