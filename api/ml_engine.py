from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class StudentMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
        )

    def compute_matches(self, target_profile, all_profiles, top_n=10, min_score=0.3):
      
        # If the target profile is not academically complete, do not compute matches
        if not getattr(target_profile, 'is_academic_complete', lambda: True)():
            return []

        # Only consider candidates that are academically complete
        candidates_qs = all_profiles.exclude(id=target_profile.id)
        candidates = [p for p in candidates_qs if getattr(p, 'is_academic_complete', lambda: True)()]
        if not candidates:
            return []

        # Build feature texts
        target_text = target_profile.get_feature_text()
        all_texts = [target_text] + [p.get_feature_text() for p in candidates]

        # TF-IDF vectorize
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Compute cosine similarity of target vs all others
        target_vector = tfidf_matrix[0:1]
        other_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(target_vector, other_vectors).flatten()

        # Apply bonus for shared attributes
        for i, profile in enumerate(candidates):
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

        # Rank and return top N filtering by min_score
        ranked_indices = np.argsort(similarities)[::-1]
        results = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            if score < min_score:
                continue
            reasons = self._generate_match_reasons(target_profile, candidates[idx])
            results.append((candidates[idx], score, reasons))
            if len(results) >= top_n:
                break

        return results

    def _generate_match_reasons(self, profile_a, profile_b):
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

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
        )

    def recommend(self, student_profile, resources, top_n=10):
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
