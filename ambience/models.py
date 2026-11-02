from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class MenuItem(TimestampedModel):
    """
    Aggregator-sourced fields (name, price, availability) are refreshed on sync.
    The ambient metadata block is OUR curated data and is never overwritten by sync.
    """

    class Texture(models.TextChoices):
        CRISP = "crisp", "Crisp"
        CRUNCHY = "crunchy", "Crunchy"
        CREAMY = "creamy", "Creamy"
        CHEWY = "chewy", "Chewy"
        SOFT = "soft", "Soft"
        LIQUID = "liquid", "Liquid"

    class Temperature(models.TextChoices):
        HOT = "hot", "Hot"
        WARM = "warm", "Warm"
        ROOM_TEMP = "room_temp", "Room Temperature"
        COLD = "cold", "Cold"

    class Aesthetic(models.TextChoices):
        RUSTIC = "rustic", "Rustic"
        MINIMAL = "minimal", "Minimal"
        LUXE = "luxe", "Luxe"
        STREET = "street", "Street"
        COZY = "cozy", "Cozy"
        FESTIVE = "festive", "Festive"
        COASTAL = "coastal", "Coastal"
        ZEN = "zen", "Zen"

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_items")