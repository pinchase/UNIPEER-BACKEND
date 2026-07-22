from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class SemanticMatchFeatures:
    """Numeric features for a student-to-student or student-to-resource match."""
    semantic_similarity: float
    skill_overlap: float
    course_overlap: float
    department_match: float
    schedule_compatibility: float
    collaboration_compatibility: float
    interaction_score: float = 0.0
    popularity_score: float = 0.0
    rating_score: float = 0.0

    def to_feature_dict(self) -> dict[str, float]:
        return {
            'semantic_similarity': self.semantic_similarity,
            'skill_overlap': self.skill_overlap,
            'course_overlap': self.course_overlap,
            'department_match': self.department_match,
            'schedule_compatibility': self.schedule_compatibility,
            'collaboration_compatibility': self.collaboration_compatibility,
            'interaction_score': self.interaction_score,
            'popularity_score': self.popularity_score,
            'rating_score': self.rating_score,
        }


class SemanticMatcher:
    """Compute semantic similarity using sentence embeddings and cosine similarity."""

    def __init__(self, embedding_provider: Optional[Any] = None):
        self.embedding_provider = embedding_provider

    def compute_semantic_similarity(self, left_text: str, right_text: str) -> float:
        if not left_text or not right_text:
            return 0.0
        if self.embedding_provider is None:
            return 0.0

        left_embedding = self.embedding_provider.encode([left_text])[0]
        right_embedding = self.embedding_provider.encode([right_text])[0]
        similarity = cosine_similarity([left_embedding], [right_embedding])[0][0]
        return float(np.clip(similarity, 0.0, 1.0))
