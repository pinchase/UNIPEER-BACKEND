"""
UniPeer ML Engine — Cosine similarity matching and resource recommendation.

Uses TF-IDF vectorization on student profiles (skills, interests, courses,
learning goals) and computes pairwise cosine similarity to rank matches.
Resource recommendation uses the same content-based approach.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class StudentMatcher:
    """
    ML-based student matching engine using cosine similarity
    on TF-IDF vectors of student profile features.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
        )

    def compute_matches(self, target_profile, all_profiles, top_n=10):
        """
        Compute similarity scores between a target student and all other students.

        Args:
            target_profile: StudentProfile instance
            all_profiles: QuerySet of all StudentProfile instances
            top_n: Number of top matches to return

        Returns:
            List of (profile, score, reasons) tuples sorted by score desc
        """
        profiles = list(all_profiles.exclude(id=target_profile.id))
        if not profiles:
            return []

        # Build feature texts
        target_text = target_profile.get_feature_text()
        all_texts = [target_text] + [p.get_feature_text() for p in profiles]

        # TF-IDF vectorize
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Compute cosine similarity of target vs all others
        target_vector = tfidf_matrix[0:1]
        other_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(target_vector, other_vectors).flatten()

        # Apply bonus for shared attributes
        for i, profile in enumerate(profiles):
            bonus = 0.0

            # Same department bonus
            if profile.department == target_profile.department:
                bonus += 0.05

            # Same year bonus
            if profile.year_of_study == target_profile.year_of_study:
                bonus += 0.03

            # Shared courses bonus
            target_courses = set(target_profile.courses.values_list('id', flat=True))
            profile_courses = set(profile.courses.values_list('id', flat=True))
            shared_courses = target_courses & profile_courses
            if shared_courses:
                bonus += 0.02 * len(shared_courses)

            # Shared skills bonus
            target_skills = set(target_profile.skills.values_list('id', flat=True))
            profile_skills = set(profile.skills.values_list('id', flat=True))
            shared_skills = target_skills & profile_skills
            if shared_skills:
                bonus += 0.02 * len(shared_skills)

            # Compatible collaboration preference
            if (profile.collaboration_preference == target_profile.collaboration_preference
                    or profile.collaboration_preference == 'any'
                    or target_profile.collaboration_preference == 'any'):
                bonus += 0.03

            # Schedule compatibility
            if (profile.preferred_time == target_profile.preferred_time
                    or profile.preferred_time == 'flexible'
                    or target_profile.preferred_time == 'flexible'):
                bonus += 0.02

            similarities[i] = min(1.0, similarities[i] + bonus)

        # Rank and return top N
        ranked_indices = np.argsort(similarities)[::-1][:top_n]
        results = []
        for idx in ranked_indices:
            if similarities[idx] > 0.01:
                reasons = self._generate_match_reasons(target_profile, profiles[idx])
                results.append((profiles[idx], float(similarities[idx]), reasons))

        return results

    def _generate_match_reasons(self, profile_a, profile_b):
        """Generate human-readable reasons for a match."""
        reasons = []

        # Check shared courses
        shared_courses = set(profile_a.courses.values_list('name', flat=True)) & \
                         set(profile_b.courses.values_list('name', flat=True))
        if shared_courses:
            reasons.append(f"Shared courses: {', '.join(list(shared_courses)[:3])}")

        # Check shared skills
        shared_skills = set(profile_a.skills.values_list('name', flat=True)) & \
                        set(profile_b.skills.values_list('name', flat=True))
        if shared_skills:
            reasons.append(f"Common skills: {', '.join(list(shared_skills)[:3])}")

        # Same department
        if profile_a.department == profile_b.department:
            reasons.append(f"Same department: {profile_a.department}")

        # Compatible goals
        if profile_a.collaboration_preference == profile_b.collaboration_preference:
            reasons.append(f"Both seeking: {profile_a.get_collaboration_preference_display()}")

        if not reasons:
            reasons.append("Similar academic interests and profile")

        return ' | '.join(reasons)


class ResourceRecommender:
    """
    Content-based resource recommendation engine.
    Matches student profiles against resource descriptions using TF-IDF + cosine similarity.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
        )

    def recommend(self, student_profile, resources, top_n=10):
        """
        Recommend resources for a student based on their profile.

        Args:
            student_profile: StudentProfile instance
            resources: QuerySet of Resource instances
            top_n: Number of recommendations to return

        Returns:
            List of (resource, relevance_score) tuples
        """
        resource_list = list(resources)
        if not resource_list:
            return []

        student_text = student_profile.get_feature_text()
        resource_texts = [r.get_feature_text() for r in resource_list]

        all_texts = [student_text] + resource_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        student_vector = tfidf_matrix[0:1]
        resource_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(student_vector, resource_vectors).flatten()

        # Boost by rating and popularity
        for i, resource in enumerate(resource_list):
            rating_boost = resource.rating * 0.02
            popularity_boost = min(0.05, resource.view_count * 0.001)
            similarities[i] = min(1.0, similarities[i] + rating_boost + popularity_boost)

        ranked_indices = np.argsort(similarities)[::-1][:top_n]
        results = []
        for idx in ranked_indices:
            if similarities[idx] > 0.01:
                results.append((resource_list[idx], float(similarities[idx])))

        return results
