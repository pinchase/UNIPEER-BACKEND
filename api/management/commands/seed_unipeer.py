from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
import random

from api.models import StudentProfile, Skill, Course

fake = Faker()

DEPARTMENTS = [
    "Computer Science",
    "Software Engineering",
    "Information Technology",
    "Cyber Security",
    "Data Science",
]

INTERESTS = [
    "AI, Machine Learning",
    "Web Development",
    "Networking",
    "Cyber Security",
    "Cloud Computing",
]

SKILLS = [
    "Python",
    "Java",
    "React",
    "Django",
    "SQL",
    "Networking",
]

class Command(BaseCommand):
    help = "Seed UNIPEER with fake student profiles"

    def handle(self, *args, **kwargs):
        for skill_name in SKILLS:
            Skill.objects.get_or_create(name=skill_name)

        for i in range(1, 51):
            username = f"student{i}"
            email = f"student{i}@kca.ac.ke"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name()
                }
            )

            if created:
                user.set_password("password123")
                user.save()

            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "bio": fake.sentence(),
                    "department": random.choice(DEPARTMENTS),
                    "year_of_study": random.randint(1, 4),
                    "gpa": round(random.uniform(2.8, 4.0), 2),
                    "interests": random.choice(INTERESTS),
                    "learning_goals": fake.sentence(),
                    "available_hours_per_week": random.randint(5, 20),
                }
            )

            random_skills = Skill.objects.order_by('?')[:3]
            profile.skills.set(random_skills)

        self.stdout.write(self.style.SUCCESS("50 student profiles created successfully"))