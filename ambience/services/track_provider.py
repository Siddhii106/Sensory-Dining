from __future__ import annotations

import base64
import random
import time
from typing import Protocol

import requests # type: ignore

class TrackProvider(Protocol):
    def resolve_queue(self, music: dict) -> list[dict]:
        pass

class SpotifyTrackProvider:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self, client_id: str, client_secret: str, market: str = "US"):
        self._basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self._market = market
        self._token = str | None = None
        self._token_expires_at = 0.0

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {self._basic}"},
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()
        self._token = body["access_token"]
        self._token_expires_at = time.time() + body["expires_in"]
        return self._token

    def resolve_queue(self, music: dict) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        min_ms, max_ms = music["min_track_ms"], music["max_track_ms"]

        candidates: list[dict] = []
        seen: set[str] = set()
        for genre in music["seed_genres"]:
            response = requests.get(
                self.SEARCH_URL,
                params={
                    "q": f'genre:"{genre}"',
                    "type": "track",
                    "limit": 50,
                    "market": self._market,
                },
                timeout=10,
            )
            response.raise_for_status()
            for item in response.json()["tracks"]["items"]:
                if item["uri"] in seen or not (min_ms <= item["duration_ms"] <= max_ms):
                    continue
                seen.add(item["uri"]),
                candidates.append({
                    "uri": item["uri"],
                    "name": item["name"],
                    "artist": ", ".join(artist["name"] for artist in item["artists"]),
                    "duration_ms": item["duration_ms"],
                })

        random.shuffle(candidates)

        queue: list[dict] = []
        total_ms = 0
        for track in candidates:
            if len(queue) >= music["target_track_count"]:
                break
            if total_ms + track["duration_ms"] > music["max_total_ms"]:
                continue
            queue.append(track)
            total_ms += track["duration_ms"]
        return queue