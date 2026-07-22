from __future__ import annotations

from typing import Any, Protocol

from .explanations import ExplanationEngine
from .feature_extractor import FeatureExtractor
from .semantic_matcher import SemanticMatcher
from .similarity import HybridScorer


class EmbeddingProvider(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]:
        ...


class HybridRecommendationEngine:
    """Hybrid recommendation engine combining semantic similarity, overlap, compatibility, and explainability."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None):
        self.embedding_provider = embedding_provider
        self.semantic_matcher = SemanticMatcher(embedding_provider=embedding_provider)
        self.feature_extractor = FeatureExtractor()
        self.scorer = HybridScorer(feature_extractor=self.feature_extractor)
        self.explainer = ExplanationEngine()

    def recommend_students(self, target_profile: Any, candidates: list[Any], top_n: int = 10, min_score: float = 0.3) -> list[tuple[Any, float, str]]:
        if not getattr(target_profile, 'is_academic_complete', lambda: True)():
            return []
        if not candidates:
            return []

        ranked: list[tuple[float, Any, dict[str, float], str]] = []
        for candidate in candidates:
            if candidate.id == target_profile.id:
                continue
            if not getattr(candidate, 'is_academic_complete', lambda: True)():
                continue
            semantic_similarity = self.semantic_matcher.compute_semantic_similarity(
                target_profile.get_feature_text(),
                candidate.get_feature_text(),
            )
            score, features = self.scorer.score_student_match(target_profile, candidate, semantic_similarity)
            if score < min_score:
                continue
            explanation = self.explainer.explain_student_match(target_profile, candidate, features)
            ranked.append((score, candidate, features, explanation))

        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, candidate, _, explanation in ranked[:top_n]:
            results.append((candidate, score, explanation))
        return results

    def recommend_resources(self, student_profile: Any, resources: list[Any], top_n: int = 10, min_score: float = 0.1) -> list[tuple[Any, float, str]]:
        if not resources:
            return []
        ranked: list[tuple[float, Any, dict[str, float], str]] = []

        for resource in resources:
            semantic_similarity = self.semantic_matcher.compute_semantic_similarity(
                student_profile.get_feature_text(),
                resource.get_feature_text(),
            )
            score, features = self.scorer.score_resource_match(student_profile, resource, semantic_similarity)
            if score < min_score:
                continue
            explanation = self.explainer.explain_resource_match(student_profile, resource, features)
            ranked.append((score, resource, features, explanation))

        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, resource, _, explanation in ranked[:top_n]:
            results.append((resource, score, explanation))
        return results
