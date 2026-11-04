from rest_framework import serializers # type: ignore

from ambience.models import AmbiencePreset

class VibeInputSerializer(serializers,Serializer):
    room_type = serializers.ChoiceField(choices=AmbiencePreset.RoomType.choices)
    lighting = serializers.ChoiceField(choices=AmbiencePreset.Lighting.choices)
    mood_score = serializers.IntegerField(min_value=0, max_value= 100)
    duration_minutes = serializers.ChoiceField(choices=AmbiencePreset.Duration.choices)
    audio_mode = serializers.ChoiceField(
        choices=AmbiencePreset.AudioMode.choices,
        default=AmbiencePreset.AudioMode.PLAYLIST,
    )

class ControlSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["play", "pause", "next", "previous"])