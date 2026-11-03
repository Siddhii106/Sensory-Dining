from datetime import timedelta
from typing import Protocol

from django.db import transaction
from django.utils import timezone

from ambience.models import MenuItem, Restaurant

MENU_CACHE_TTL = timedelta(minutes=15)

class AggregatorClient(Protocol):
    def fetch_menu(self, external_restaurant_id: str) -> list[dict]: ...

def sync_restaurant_menu(restaurant: Restaurant, client: AggregatorClient, force: bool = False) ->bool:
    if not force and restaurant.last_synced_at:
        if timezone.now() - restaurant.last_synced_at < MENU_CACHE_TTL:
            return False

    rows = client.fetch_menu(restaurant.external_restaurant_id)
    seen_ids = [row["external_item_id"] for row in rows]

    with transaction.atomic():
        for row in rows:
            MenuItem.objects.update_or_create(
                restaurant=restaurant,
                external_item_id=row["external_item_id"],
                defaults={
                    "name": row["name"],
                    "description": row.get("description", ""),
                    "price_minor": row["price_minor"],
                    "is_available": row["is_available"],
                },
            )

        restaurant.menu_items.exclude(external_item_id__in=seen_ids).update(is_available=False)
        restaurant.last_synced_at = timezone.now()
        restaurant.save(update_fields=["last_synced_at", "updated_at"])

    return True