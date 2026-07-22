from __future__ import annotations

from typing import Any

from .feature_extractor import FeatureExtractor
from .semantic_matcher import SemanticMatchFeatures


class HybridScorer:
    """Blend semantic, overlap, and compatibility components into a single score."""

    def __init__(self, feature_extractor: FeatureExtractor | None = None):
        self.feature_extractor = feature_extractor or FeatureExtractor()

    def score_student_match(self, profile_a: Any, profile_b: Any, semantic_similarity: float, features: SemanticMatchFeatures | None = None) -> tuple[float, dict[str, float]]:
        extracted = self.feature_extractor.extract_student_features(profile_a, profile_b)
        if features is None:
            features = SemanticMatchFeatures(
                semantic_similarity=semantic_similarity,
                skill_overlap=extracted['skill_overlap'],
                course_overlap=extracted['course_overlap'],
                department_match=extracted['department_match'],
                schedule_compatibility=extracted['schedule_compatibility'],
                collaboration_compatibility=extracted['collaboration_compatibility'],
            )

        final_score = (
            0.50 * features.semantic_similarity
            + 0.20 * features.skill_overlap
            + 0.10 * features.course_overlap
            + 0.10 * features.collaboration_compatibility
            + 0.05 * features.schedule_compatibility
            + 0.05 * features.department_match
        )
        return round(min(1.0, max(0.0, final_score)), 4), features.to_feature_dict()

    def score_resource_match(self, student_profile: Any, resource: Any, semantic_similarity: float) -> tuple[float, dict[str, float]]:
        extracted = self.feature_extractor.extract_resource_features(student_profile, resource)
        final_score = (
            0.60 * semantic_similarity
            + 0.20 * extracted['skill_overlap']
            + 0.10 * extracted['course_overlap']
            + 0.05 * extracted['rating_score']
            + 0.05 * extracted['popularity_score']
        )
        return round(min(1.0, max(0.0, final_score)), 4), {
            'semantic_similarity': semantic_similarity,
            'skill_overlap': extracted['skill_overlap'],
            'course_overlap': extracted['course_overlap'],
            'popularity_score': extracted['popularity_score'],
            'rating_score': extracted['rating_score'],
        }
