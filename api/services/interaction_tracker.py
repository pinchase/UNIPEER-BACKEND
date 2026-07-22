from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class InteractionEvent:
    """Represents a user interaction that can later be used for ML training."""
    interaction_type: str
    source_user: Any
    target_user: Any | None = None
    target_resource: Any | None = None
    metadata: dict | None = None


class InteractionTracker:
    """Collects interaction events for future recommendation model training."""

    def __init__(self):
        self.events: list[InteractionEvent] = []

    def record(self, event: InteractionEvent) -> None:
        self.events.append(event)

    def snapshot(self) -> list[InteractionEvent]:
        return list(self.events)
