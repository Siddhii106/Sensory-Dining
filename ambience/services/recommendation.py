from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

from ambience.models import Order

AVG_TRACK_SECONDS = 210
MIN_TRACK_SECONDS = 90
MAX_TRACK_SECONDS = 600
FOOD_WEIGHT = 0.60
MOOD_WEIGHT = 0.40
MAX_SEEDS = 5

MOOD_GENRE_TIERS = (
    (0.40, ["ambient", "sleep", "acoustic"]),
    (0.70, ["chill", "jazz", "indie"]),
    (1.01, ["happy", "groove", "pop"]),
)

ROOM_MODIFIERS = {
    "couch": {"acousticness": +0.10, "energy": -0.05, "tempo": -4.0},
    "table": {"acousticness": +0.05, "energy": 0.00, "tempo": 0.0},
    "desk": {"acousticness": -0.10, "energy": -0.08, "tempo": -8.0},     
}

LIGHTING_MODIFIERS = {
    "dim": {"energy": -0.05, "valence": -0.05},
    "bright": {"energy": +0.05, "valence": +0.05},
    "screen_glow": {"acousticness": -0.05, "tempo": +2.0},
}

ROOM_SOUNDSCAPE = {"couch": "fireplace", "table": "cafe_murmur", "desk": "brown_noise"}
SOUNDSCAPE_VOLUMES = (0.70, 0.50, 0.35)

@dataclass(frozen=True)
class VibeInput:
    room_type: str
    lighting: str
    mood_score: int
    duration_minutes: int
    audio_mode: str = "playlist"

@dataclass
class MusicCriteria:
    target_tempo: float
    target_energy: float
    target_valence: float
    target_acousticness: float
    seed_genres: list[str]
    target_track_count: int
    min_track_ms: int
    max_track_ms: int
    max_total_ms: int

@dataclass
class SoundscapeLayer:
    tag: str
    volume: float

@dataclass
class AmbiencePayload:
    audio_mode: str
    duration_ms: int
    music: MusicCriteria | None = None
    soundscape: list[SoundscapeLayer]= field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

class AmbienceUnavailable(ValueError):
    pass

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))

def _blend(food_value: float, mood_value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return _clamp(
        FOOD_WEIGHT * food_value + MOOD_WEIGHT * mood_value, lo, hi
    )

def _mood_baseline(m: float) -> dict[str, float]:
    return {
        "tempo": 75 + 65 * m,
        "energy": 0.15 + 0.75 * m,
        "valence": 0.25 + 0.60 * m,
        "acousticness": 0.60 - 0.50 * m,
    }

    