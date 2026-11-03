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

def _apply_room_and_lighting(base: dict[str, float], vibe:VibeInput) -> dict[str, float]:
    adjusted = dict(base)
    for modifiers in (ROOM_MODIFIERS[vibe.room_type], LIGHTING_MODIFIERS[vibe.lighting]):
        for key, delta in modifiers.items():
            adjusted[key] += delta
    return adjusted

def _summarize_plate(order: Order) -> dict:
    total_qty = 0
    tempo = energy = valence = acousticness = spice = warm_qty = 0.0
    genres: Counter[str] = Counter()
    soundscapes: Counter[str] = Counter()

    for line in order.items.all():
        item = line.menu_item
        qty = line.quantity
        total_qty += qty
        tempo += item.tempo * qty
        valence += item.valence * qty
        acousticness += item.acousticness * qty
        spice += item.spice * qty
        if item.temperature in (item.Temperature.WARM, item.Temperature.HOT):
            warm_qty += qty
        for genre in item.genre_tags:
            genres[genre] += qty
        for tag in item.soundscape_tags:
            soundscapes[tag] += qty

    if total_qty == 0:
        raise AmbienceUnavailable("Order has no items to build an ambience from.")
    
    return {
        "tempo": tempo / total_qty,
        "energy": energy / total_qty,
        "valence": valence / total_qty,
        "acousticness": acousticness / total_qty,
        "spice": (spice / total_qty) / 5.0,
        "warmth": warm_qty / total_qty,
        "genres": genres,
        "soundscapes": soundscapes,
    }

def _pick_genres(plate: dict, m: float) -> list[str]:
    mood_seeds = next(seeds for ceiling, seeds in MOOD_GENRE_TIERS if m < ceiling)
    food_seeds = [genre for genre, _ in plate["genres"].most_common(2)]
    merged = list(dict.fromkeys(mood_seeds + food_seeds))
    return merged[:MAX_SEEDS]

def _build_music(plate: dict, blended: dict[str, float], m: float, duration_ms: int) -> MusicCriteria:
    track_count = max(1, round((duration_ms / 1000) / AVG_TRACK_SECONDS))
    return MusicCriteria(
        target_tempo=round(blended["tempo"], 1),
        target_energy=round(blended["energy"], 3),
        target_valence=round(blended["valence"], 3),
        target_acousticness=round(blended["acousticness"], 3),
        seed_genres=_pick_genres(plate, m),
        target_track_count=track_count,
        min_track_ms=MIN_TRACK_SECONDS * 1000,
        max_track_ms=MAX_TRACK_SECONDS * 1000,
        max_total_ms=duration_ms,
    )

def _build_soundscape(plate: dict, room_type: str) -> list[SoundscapeLayer]:
    tags = [tag for tag, _ in plate["soundscapes"].most_common(2)]
    room_tag = ROOM_SOUNDSCAPE[room_type]
    if room_tag not in tags:
        tags.append(room_tag)
    return [
        SoundscapeLayer(tag=tag, volume=volume)
        for tag, volume in zip(tags[:3], SOUNDSCAPE_VOLUMES)
    ]

def build_ambience_payload(order: Order, vibe: VibeInput) -> AmbiencePayload:

    if not order.items.exists():
        raise AmbienceUnavailable("Ambience is unavailable for cancelled orders.")

    plate = _summarize_plate(order)
    m = vibe.mood_score / 100.0
    duration_ms = vibe.duration_minutes * 60_000

    if vibe.audio_mode == "soundscape":
        return AmbiencePayload(
            audio_mode="soundscape",
            duration_ms=duration_ms,
            soundscape=_build_soundscape(plate, vibe.room_type),
        )

    food = {
        "tempo" :plate["tempo"],
        "energy": _clamp(plate["energy"] + 0.10 * plate["spice"]),
        "valence": _clamp(plate["valence"] + 0.05 * plate["spice"]),
        "acousticness": _clamp(plate["acousticness"] + 0.08 * plate["warmth"])
    }

    mood = _apply_room_and_lighting(_mood_baseline(m), vibe)

    blended = {
        "tempo": _blend(food["tempo"], mood["tempo"], lo=60, hi=170),
        "energy": _blend(food["energy"], mood["energy"]),
        "valence": _blend(food["valence"], mood["valence"]),
        "acousticness": _blend(food["acousticness"], mood["acousticness"]),
    }

    return AmbiencePayload(
        audio_mode="playlist",
        duration_ms=duration_ms,
        music=_build_music(plate, blended, m, duration_ms),
    )

def to_spotify_recommendation_params(criteria: MusicCriteria) -> dict:
    return {
        "limit": criteria.target_track_count,
        "seed_genres": round(criteria.target_tempo),
        "target_tempo": criteria.target_energy,
        "target_valence": criteria.target_valence,
        "target_acousticness": criteria.target_acousticness,
        "min_duration_ms": criteria.min_track_ms,
        "max_duration_ms": criteria.max_track_ms,
    }