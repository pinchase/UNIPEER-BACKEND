from __future__ import annotations

from typing import Any

from .services.recommendation_engine import HybridRecommendationEngine


class StudentMatcher:
    """Compatibility matcher for student-to-student recommendations."""

    def __init__(self, engine: HybridRecommendationEngine | None = None):
        self.engine = engine or HybridRecommendationEngine()

    def compute_matches(self, target_profile, all_profiles, top_n=10, min_score=0.3):
        candidates = [p for p in list(all_profiles) if p.id != target_profile.id]
        results = self.engine.recommend_students(target_profile, candidates, top_n=top_n, min_score=min_score)
        return results

    def _generate_match_reasons(self, profile_a, profile_b):
        return self.engine.explainer.explain_student_match(profile_a, profile_b, {
            'skill_overlap': 0.0,
            'course_overlap': 0.0,
            'department_match': 1.0 if profile_a.department == profile_b.department else 0.0,
            'schedule_compatibility': 1.0 if profile_a.preferred_time == profile_b.preferred_time else 0.0,
            'collaboration_compatibility': 1.0 if profile_a.collaboration_preference == profile_b.collaboration_preference else 0.0,
            'semantic_similarity': 0.0,
        })


class ResourceRecommender:
    """Resource recommender for student-to-resource recommendations."""

    def __init__(self, engine: HybridRecommendationEngine | None = None):
        self.engine = engine or HybridRecommendationEngine()

    def recommend(self, student_profile, resources, top_n=10):
        resource_list = list(resources)
        results = self.engine.recommend_resources(student_profile, resource_list, top_n=top_n)
        return [(resource, score) for resource, score, _ in results]
