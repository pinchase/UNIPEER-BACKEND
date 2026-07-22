from __future__ import annotations

from typing import Any


class ExplanationEngine:
    """Convert numeric features into human-readable recommendation reasons."""

    def explain_student_match(self, profile_a: Any, profile_b: Any, feature_dict: dict[str, float]) -> str:
        reasons: list[str] = []
        if feature_dict.get('skill_overlap', 0.0) > 0.0:
            reasons.append(f"{int(round(feature_dict['skill_overlap'] * 100))}% skill overlap")
        if feature_dict.get('course_overlap', 0.0) > 0.0:
            reasons.append(f"{int(round(feature_dict['course_overlap'] * 100))}% course overlap")
        if feature_dict.get('department_match', 0.0) > 0.0:
            reasons.append('same department')
        if feature_dict.get('schedule_compatibility', 0.0) > 0.0:
            reasons.append('compatible study schedule')
        if feature_dict.get('collaboration_compatibility', 0.0) > 0.0:
            reasons.append('compatible collaboration preference')
        if feature_dict.get('semantic_similarity', 0.0) > 0.3:
            reasons.append('similar academic interests')
        if not reasons:
            reasons.append('shared profile signals')
        return '; '.join(reasons)

    def explain_resource_match(self, student_profile: Any, resource: Any, feature_dict: dict[str, float]) -> str:
        reasons: list[str] = []
        if feature_dict.get('skill_overlap', 0.0) > 0.0:
            reasons.append(f"{int(round(feature_dict['skill_overlap'] * 100))}% skill relevance")
        if feature_dict.get('course_overlap', 0.0) > 0.0:
            reasons.append(f"{int(round(feature_dict['course_overlap'] * 100))}% course relevance")
        if feature_dict.get('rating_score', 0.0) > 0.0:
            reasons.append('high-rated resource')
        if feature_dict.get('popularity_score', 0.0) > 0.0:
            reasons.append('popular resource')
        if not reasons:
            reasons.append('content matches your profile')
        return '; '.join(reasons)
