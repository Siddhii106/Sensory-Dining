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

class Restaurant(TimestampedModel):
    """
    A restaurant mirrored from the aggregator. We store identifiers and
    display metadata plus sync bookkeeping. Menus are cached, never scraped.
    """
    external_restaurant_id = models.CharField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    cuisine = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

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
    external_item_id = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_minor = models.PositiveIntegerField(help_text="Price in minor units (e.g. paise).")
    is_available = models.BooleanField(default=True)

    # ---- Culinary ambient metadata (curated in-house) ----
    texture = models.CharField(max_length=20, choices=Texture.choices, blank=True)
    temperature = models.CharField(max_length=20, choices=Temperature.choices, blank=True)
    aesthetic = models.CharField(max_length=20, choices=Aesthetic.choices, blank=True)
    spice_level = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(5)])
    tempo_bpm = models.PositiveSmallIntegerField(default=100, validators=[MinValueValidator(40), MaxValueValidator(200)])
    energy = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    valence = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    acousticness = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    genre_tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    soundscape_tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "external_item_id"],
                name="unique_menu_item_per_restaurant",
            ),
        ] 
        indexes = [models.Index(fields=["restaurant", "is_available"])]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

class Order(TimestampedModel):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PREPARING = "preparing", "Preparing"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name="orders")
    external_order_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    placed_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-placed_at"]
        indexes = [models.Index(fields=["user", "status"])]

    @property
    def is_ambience_ready(self) -> bool:
        return self.status == self.Status.DELIVERED

    def __str__(self):
        return f"Order {self.external_order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])

class AmbiencePreset(TimestampedModel):

    class RoomType(models.TextChoices):
        COUCH = "couch", "Couch"
        TABLE = "table", "Table"
        DESK = "desk", "Desk"

    class Lighting(models.TextChoices):
        DIM = "dim", "Dim"
        BRIGHT = "bright", "Bright"
        SCREEN_GLOW = "screen_glow", "Screen Glow"

    class AudioMode(models.TextChoices):
        PLAYLIST = "playlist", "Playlist"
        SOUNDSCAPE = "soundscape", "Soundscape"

    class Duration(models.TextChoices):
        SHORT = 15, "15 minutes"
        MEDIUM = 30, "30 minutes"
        LONG = 60, "60 minutes"
        
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ambience_presets")
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, null=True, blank=True, related_name="ambience"
    )
    name = models.CharField(max_length=80, blank=True)
    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    lighting = models.CharField(max_length=20, choices=Lighting.choices)
    mood_score = models.PositiveSmallIntegerField(
        default=50, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    duration_minutes = models.PositiveSmallIntegerField(choices=Duration.choices, default=Duration.STANDARD)
    audio_mode = models.CharField(max_length=12, choices=AudioMode.choices, default=AudioMode.PLAYLIST)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"Preset {self.pk}"