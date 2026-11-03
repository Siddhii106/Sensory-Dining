from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ambience.models import AmbiencePreset, AmbienceSession, Order
from ambience.services.recommendation import (
    AmbienceUnavailable,
    VibeInput,
    build_ambience_payload,
)
from ambience.services.track_provider import TrackProvider

PlaybackState = AmbienceSession.PlaybackState
VALID_ACTIONS = {"play", "pause", "next", "previous"}

class SessionError(AmbienceUnavailable):

    def start_session(order: Order, vibe: VibeInput, provider: TrackProvider) ->AmbienceSession:
        payload = build_ambience_payload(order, vibe)
        criteria = payload.to_dict()

        timer_started_at = order.placed_at
        ends_at = timer_started_at + timedelta(milliseconds=payload.duration_ms)
        if timezone.now() >= ends_at:
            raise SessionError("This meal's timer has already run out.")

        tracks: list[dict] = []
        if payload.audio_mode == "playlist":
            tracks = provider.resolve_queue(criteria["music"])
            if not tracks:
                raise SessionError(
                    "We couldn't assemble a playlist for this mix. Try another mood or meal length."
                )

            with transaction.atomic():
                session, _ = AmbienceSession.objects.update_or_create(
                    order=order,
                    defaults={
                        "criteria": criteria,
                        "track_queue": tracks,
                        "tracks_index": 0,
                        "playback_state": PlaybackState.READY,
                        "timer_started_at": timer_started_at,
                        "duration_ms": payload.duration_ms,
                    },
                )
                AmbiencePreset.objects.update_or_create(
                    order=order,
                    defaults={
                        "user": order.user,
                        "room_type": vibe.room_type,
                        "lighting": vibe.lighting,
                        "mood_score": vibe.mood_score,
                        "duration_minutes": vibe.duration_minutes,
                        "audio_mode": vibe.audio_mode,
                    },
                )
                return session
            def apply_control(session: AmbienceSession, action: str) -> AmbienceSession:
                if action not in VALID_ACTIONS:
                    raise SessionError("Unknown playback action.")
                if session.is_expired and action != "pause":
                    raise SessionError("The meal timer has run out.")

                queue_len = len(session.track_queue)

                if action == "pause":
                    session.playback_state = PlaybackState.PAUSED

                elif action == "play":
                    if session.playback_state == PlaybackState.ENDED and queue_len:
                        session.track_index = 0
                    session.playback_state = PlaybackState.PLAYING

                else:
                    if queue_len == 0:
                        raise SessionError("Track controls are only available for playlists.")
                    if action == "previous":
                        session.track_index = max(0, session.track_index - 1)
                        session.playback_state = PlaybackState.PLAYING
                    elif session.track_index + 1 < queue_len:
                        session.track_index += 1
                        session.playback_state = PlaybackState.PLAYING
                    else:
                        session.playback_state = PlaybackState.ENDED

                session.save(update_fields=["track_index", "playback_state", "updated_at"])
                return session

            def session_state(session: AmbienceSession) -> dict:
                queue = session.track_queue
                index = session.track_index
                return {
                    "audio_mode": session.criteria["audio_mode"],
                    "playback_state": session.playback_state,
                    "track_index": index,
                    "track_count": len(queue),
                    "current_track": queue[index] if queue and index < len(queue) else None,
                    "soundscape": session.criteria.get("soundscape", []),
                    "expires_at": session.expires_at.isoformat(),
                    "remaining_ms": session.remaining_ms(),
                }