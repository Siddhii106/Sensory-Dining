from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ambience.models import AmbienceSession, Order
from ambience.serializers import ControlSerializer, VibeInputSerializer
from ambience.services.session import AmbienceUnavailable, VibeInput
from ambience.services.session import apply_control, session_state, start_session
from ambience.services.track_provider import SpotifyTrackProvider

track_provider = SpotifyTrackProvider(
    settings.SPOTIFY_CLIENT_ID,
    settings.SPOTIFY_CLIENT_SECRET,
)

def _owned_session(request, order_id: int) -> AmbienceSession:
    return get_object_or_404(
        AmbienceSession.objects.select_related("order"),
        order__pk=order_id,
        order__user=request.user,
    )

class AmbienceSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id: int):
        from ambience.services.session import session_state

        return Response(session_state(_owned_session(request, order_id)))

    def post(self, request, order_id: int):
        order = get_object_or_404(
            Order.objects.prefetch_related("items__menu_item"),
            pk=order_id,
            user=request.user,
        )
        serializer = VibeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vibe = VibeInput(**serializer.validated_data)

        try:
            session = start_session(order, vibe, track_provider)
        except AmbienceUnavailable as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(session_state(session), status=status.HTTP_201_CREATED)

class AmbienceControlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id: int):
        order = get_object_or_404(
            Order.objects.select_related("restaurant").prefetch_related("items__menu_item"),
            pk=order_id,
            user=request.user,
        )

        serializer = VibeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        vibe = VibeInput(
            room_type=data["room_type"],
            lighting=data["lighting"],
            mood_score=data["mood_score"],
            duration_minutes=data["duration_minutes"],
            audio_mode=data["audio_mode"],
        )

        try:
            payload = build_ambience_payload(order, vibe)
        except AmbienceUnavailable as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        AmbiencePreset.objects.update_or_create(
            order=order,
            defaults={
                "user": request.user,
                "room_type": vibe.room_type,
                "lighting": vibe.lighting,
                "mood_score": vibe.mood_score,
                "duration_minutes": vibe.duration_minutes,
                "audio_mode": vibe.audio_mode,
            },
        )

        return Response(payload.to_dict(), status=status.HTTP_200_OK)