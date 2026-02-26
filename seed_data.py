import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unipeer.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import StudentProfile, Skill, Course, Resource

def seed():
    print("🌱 Seeding academic data...")
    
    # 1. Create Skills
    skills_data = [
        ('Python', 'programming'), ('Java', 'programming'), ('C++', 'programming'),
        ('JavaScript', 'programming'), ('React', 'programming'), ('Django', 'programming'),
        ('Calculus', 'mathematics'), ('Linear Algebra', 'mathematics'), ('Probability', 'mathematics'),
        ('Organic Chemistry', 'science'), ('Genetics', 'science'), ('Thermodynamics', 'science'),
        ('Graphic Design', 'design'), ('UI/UX', 'design'), ('Digital Marketing', 'business'),
        ('Financial Accounting', 'business'), ('Microeconomics', 'business'), ('Legal Writing', 'other'),
    ]
    
    created_skills = []
    for name, cat in skills_data:
        skill, _ = Skill.objects.get_or_create(name=name, defaults={'category': cat})
        created_skills.append(skill)
    
    # 2. Create Courses
    courses_data = [
        ('CS101', 'Intro to Computer Science', 'Computer Science', 100),
        ('CS302', 'Data Structures & Algorithms', 'Computer Science', 300),
        ('LAW110', 'Introduction to Law', 'Law', 100),
        ('MED205', 'Human Anatomy', 'Medicine', 200),
        ('ENG401', 'Advanced Engineering Design', 'Engineering', 400),
        ('BUS101', 'Principles of Management', 'Business', 100),
        ('MAT201', 'Multivariable Calculus', 'Mathematics', 200),
    ]
    
    created_courses = []
    for code, name, dept, lvl in courses_data:
        course, _ = Course.objects.get_or_create(
            code=code, 
            defaults={'name': name, 'department': dept, 'level': lvl}
        )
        created_courses.append(course)
    
    # 3. Create Resources
    print("📚 Creating resources...")
    resources = [
        {
            'title': 'The Python Handbook',
            'description': 'A comprehensive guide to modern Python development.',
            'type': 'textbook',
            'difficulty': 'beginner',
            'tags': 'python, programming, basics',
            'skills': ['Python'],
            'courses': ['CS101']
        },
        {
            'title': 'Anatomy Visualization Masterclass',
            'description': 'High-resolution 3D models for medical students.',
            'type': 'video',
            'difficulty': 'intermediate',
            'tags': 'medicine, anatomy, health',
            'skills': ['Genetics'],
            'courses': ['MED205']
        },
        {
            'title': 'Data Structures Illustrated',
            'description': 'Visual guide to stacks, queues, and trees.',
            'type': 'tutorial',
            'difficulty': 'intermediate',
            'tags': 'cs, algorithms, data structures',
            'skills': ['Java', 'C++'],
            'courses': ['CS302']
        }
    ]
    
    for r in resources:
        res, _ = Resource.objects.get_or_create(
            title=r['title'],
            defaults={
                'description': r['description'],
                'resource_type': r['type'],
                'difficulty': r['difficulty'],
                'tags': r['tags'],
                'url': 'https://example.com/resource'
            }
        )
        for s_name in r['skills']:
            s = Skill.objects.filter(name=s_name).first()
            if s: res.related_skills.add(s)
        for c_code in r['courses']:
            c = Course.objects.filter(code=c_code).first()
            if c: res.related_courses.add(c)

    print("✅ Seeding complete!")

if __name__ == "__main__":
    seed()
