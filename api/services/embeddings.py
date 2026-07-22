from __future__ import annotations

from typing import Any


class EmbeddingStore:
    """Simple embedding store interface designed for future replacement by vector DB backends."""

    def __init__(self):
        self._store: dict[str, list[float]] = {}

    def set(self, key: str, embedding: list[float]) -> None:
        self._store[key] = embedding

    def get(self, key: str) -> list[float] | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
