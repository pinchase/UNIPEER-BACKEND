from __future__ import annotations

from typing import Any


class RecommendationAutomation:
    """Thin automation wrapper that can later be hooked into Celery or Django-Q."""

    def __init__(self, engine: Any):
        self.engine = engine

    def handle_profile_updated(self, profile: Any, candidates: list[Any]) -> list[tuple[Any, float, str]]:
        return self.engine.recommend_students(profile, candidates)

    def handle_resource_created(self, student_profile: Any, resources: list[Any]) -> list[tuple[Any, float, str]]:
        return self.engine.recommend_resources(student_profile, resources)
