from __future__ import annotations

from typing import Any

from django.db.models import Q


class FeatureExtractor:
    """Extract reusable numeric features for student and resource recommendations."""

    def extract_student_features(self, profile_a: Any, profile_b: Any) -> dict[str, float]:
        skill_names_a = set(profile_a.skills.values_list('name', flat=True))
        skill_names_b = set(profile_b.skills.values_list('name', flat=True))
        course_names_a = set(profile_a.courses.values_list('name', flat=True))
        course_names_b = set(profile_b.courses.values_list('name', flat=True))
        interest_names_a = set((profile_a.interests or '').lower().replace('-', ' ').split())
        interest_names_b = set((profile_b.interests or '').lower().replace('-', ' ').split())

        skill_overlap = self._jaccard(skill_names_a, skill_names_b)
        course_overlap = self._jaccard(course_names_a, course_names_b)
        interest_overlap = self._jaccard(interest_names_a, interest_names_b)
        department_match = 1.0 if profile_a.department == profile_b.department else 0.0
        schedule_compatibility = 1.0 if self._schedules_match(profile_a, profile_b) else 0.0
        collaboration_compatibility = 1.0 if self._collaboration_compatible(profile_a, profile_b) else 0.0

        return {
            'skill_overlap': skill_overlap,
            'course_overlap': course_overlap,
            'interest_overlap': interest_overlap,
            'department_match': department_match,
            'schedule_compatibility': schedule_compatibility,
            'collaboration_compatibility': collaboration_compatibility,
        }

    def extract_resource_features(self, student_profile: Any, resource: Any) -> dict[str, float]:
        skill_names = set(resource.related_skills.values_list('name', flat=True))
        course_names = set(resource.related_courses.values_list('name', flat=True))
        student_skills = set(student_profile.skills.values_list('name', flat=True))
        student_courses = set(student_profile.courses.values_list('name', flat=True))

        return {
            'skill_overlap': self._jaccard(student_skills, skill_names),
            'course_overlap': self._jaccard(student_courses, course_names),
            'popularity_score': min(1.0, resource.view_count / 1000.0),
            'rating_score': min(1.0, resource.rating / 5.0),
        }

    def _jaccard(self, left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _schedules_match(self, profile_a: Any, profile_b: Any) -> bool:
        return (
            profile_a.preferred_time == profile_b.preferred_time
            or profile_a.preferred_time == 'flexible'
            or profile_b.preferred_time == 'flexible'
        )

    def _collaboration_compatible(self, profile_a: Any, profile_b: Any) -> bool:
        return (
            profile_a.collaboration_preference == profile_b.collaboration_preference
            or profile_a.collaboration_preference == 'any'
            or profile_b.collaboration_preference == 'any'
        )
