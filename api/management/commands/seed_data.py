"""
Management command to seed the database with demo data for UniPeer.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Skill, Course, StudentProfile, Resource, CollaborationRoom
import random


class Command(BaseCommand):
    help = 'Seed the database with demo data for UniPeer'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding UniPeer database...\n')

        # ─── Skills ───
        skill_data = [
            ('Python', 'programming'), ('JavaScript', 'programming'), ('Java', 'programming'),
            ('C++', 'programming'), ('React', 'programming'), ('Django', 'programming'),
            ('Machine Learning', 'programming'), ('Data Analysis', 'programming'),
            ('SQL', 'programming'), ('HTML/CSS', 'programming'),
            ('Calculus', 'mathematics'), ('Linear Algebra', 'mathematics'),
            ('Statistics', 'mathematics'), ('Probability', 'mathematics'),
            ('Physics', 'science'), ('Chemistry', 'science'), ('Biology', 'science'),
            ('English Writing', 'language'), ('Technical Writing', 'language'),
            ('UI/UX Design', 'design'), ('Graphic Design', 'design'),
            ('Project Management', 'business'), ('Data Visualization', 'business'),
            ('Circuit Design', 'engineering'), ('Embedded Systems', 'engineering'),
            # Universal skills
            ('Research Methods', 'academic'), ('Critical Thinking', 'academic'),
            ('Public Speaking', 'communication'), ('Academic Writing', 'language'),
            ('Clinical Assessment', 'health'), ('Patient Care', 'health'),
            ('Pharmacology', 'health'), ('Anatomy', 'health'),
            ('Psychology', 'social_science'), ('Sociology', 'social_science'),
            ('Economics', 'business'), ('Accounting', 'business'),
            ('Marketing', 'business'), ('Financial Analysis', 'business'),
            ('Music Theory', 'arts'), ('Drawing & Painting', 'arts'),
            ('Creative Writing', 'arts'), ('Legal Research', 'law'),
            ('Environmental Science', 'science'), ('Nutrition', 'health'),
        ]
        skills = {}
        for name, category in skill_data:
            skill, _ = Skill.objects.get_or_create(name=name, defaults={'category': category})
            skills[name] = skill
        self.stdout.write(f'  ✅ Created {len(skills)} skills')

        # ─── Courses ───
        course_data = [
            ('CS101', 'Introduction to Computer Science', 'Computer Science', 100),
            ('CS201', 'Data Structures & Algorithms', 'Computer Science', 200),
            ('CS301', 'Software Engineering', 'Computer Science', 300),
            ('CS302', 'Artificial Intelligence', 'Computer Science', 300),
            ('CS303', 'Database Systems', 'Computer Science', 300),
            ('CS401', 'Machine Learning', 'Computer Science', 400),
            ('CS402', 'Distributed Systems', 'Computer Science', 400),
            ('MTH101', 'Calculus I', 'Mathematics', 100),
            ('MTH201', 'Linear Algebra', 'Mathematics', 200),
            ('MTH301', 'Probability & Statistics', 'Mathematics', 300),
            ('PHY101', 'Physics I', 'Physics', 100),
            ('ENG201', 'Technical Communication', 'English', 200),
            ('BUS301', 'Project Management', 'Business', 300),
            ('ECE201', 'Digital Electronics', 'Electrical Engineering', 200),
            ('ECE301', 'Embedded Systems', 'Electrical Engineering', 300),
            # Universal courses
            ('PSY101', 'Introduction to Psychology', 'Psychology', 100),
            ('PSY301', 'Abnormal Psychology', 'Psychology', 300),
            ('ECO101', 'Principles of Economics', 'Economics', 100),
            ('ECO301', 'Microeconomic Analysis', 'Economics', 300),
            ('NUR201', 'Fundamentals of Nursing', 'Nursing', 200),
            ('NUR301', 'Clinical Practice I', 'Nursing', 300),
            ('LAW201', 'Constitutional Law', 'Law', 200),
            ('ART201', 'Visual Arts & Design', 'Fine Arts', 200),
            ('EDU301', 'Educational Psychology', 'Education', 300),
            ('PHL201', 'Ethics & Philosophy', 'Philosophy', 200),
        ]
        courses = {}
        for code, name, dept, level in course_data:
            course, _ = Course.objects.get_or_create(
                code=code, defaults={'name': name, 'department': dept, 'level': level}
            )
            courses[code] = course
        self.stdout.write(f'  ✅ Created {len(courses)} courses')

        # ─── Student Profiles ───
        students_data = [
            {
                'username': 'amina_k', 'first': 'Amina', 'last': 'Kimani',
                'email': 'amina@uni.ac.ke', 'dept': 'Computer Science',
                'year': 3, 'interests': 'machine learning, data science, AI, neural networks',
                'goals': 'Build ML models for healthcare', 'pref': 'project',
                'skills': ['Python', 'Machine Learning', 'Data Analysis', 'Statistics'],
                'courses': ['CS301', 'CS302', 'CS401', 'MTH301'],
                'bio': 'Passionate about using AI to solve real-world problems in healthcare.',
            },
            {
                'username': 'brian_o', 'first': 'Brian', 'last': 'Ochieng',
                'email': 'brian@uni.ac.ke', 'dept': 'Computer Science',
                'year': 3, 'interests': 'web development, full stack, APIs, cloud',
                'goals': 'Master full-stack development', 'pref': 'study_group',
                'skills': ['JavaScript', 'React', 'Django', 'SQL', 'HTML/CSS'],
                'courses': ['CS301', 'CS303', 'CS201'],
                'bio': 'Full-stack developer building web apps to connect communities.',
            },
            {
                'username': 'cynthia_w', 'first': 'Cynthia', 'last': 'Wanjiku',
                'email': 'cynthia@uni.ac.ke', 'dept': 'Mathematics',
                'year': 2, 'interests': 'statistics, data analysis, probability, R programming',
                'goals': 'Apply statistics to social research', 'pref': 'research',
                'skills': ['Statistics', 'Probability', 'Data Analysis', 'Python'],
                'courses': ['MTH201', 'MTH301', 'CS101'],
                'bio': 'Mathematics student who loves finding patterns in data.',
            },
            {
                'username': 'david_m', 'first': 'David', 'last': 'Mwangi',
                'email': 'david@uni.ac.ke', 'dept': 'Computer Science',
                'year': 4, 'interests': 'distributed systems, cloud computing, microservices',
                'goals': 'Design scalable distributed applications', 'pref': 'project',
                'skills': ['Java', 'Python', 'SQL', 'Project Management'],
                'courses': ['CS402', 'CS301', 'CS303', 'BUS301'],
                'bio': 'Senior CS student researching distributed systems for developing markets.',
            },
            {
                'username': 'esther_n', 'first': 'Esther', 'last': 'Njeri',
                'email': 'esther@uni.ac.ke', 'dept': 'Electrical Engineering',
                'year': 3, 'interests': 'embedded systems, IoT, robotics, Arduino',
                'goals': 'Build IoT solutions for agriculture', 'pref': 'project',
                'skills': ['C++', 'Circuit Design', 'Embedded Systems', 'Python'],
                'courses': ['ECE301', 'ECE201', 'PHY101', 'CS101'],
                'bio': 'Engineering student passionate about IoT for smart farming.',
            },
            {
                'username': 'felix_k', 'first': 'Felix', 'last': 'Kiprop',
                'email': 'felix@uni.ac.ke', 'dept': 'Computer Science',
                'year': 2, 'interests': 'AI, deep learning, computer vision, NLP',
                'goals': 'Research computer vision applications', 'pref': 'research',
                'skills': ['Python', 'Machine Learning', 'Linear Algebra', 'Calculus'],
                'courses': ['CS201', 'CS302', 'MTH201', 'MTH101'],
                'bio': 'Aspiring AI researcher exploring visual understanding systems.',
            },
            {
                'username': 'grace_a', 'first': 'Grace', 'last': 'Achieng',
                'email': 'grace@uni.ac.ke', 'dept': 'Computer Science',
                'year': 3, 'interests': 'UI/UX, human-computer interaction, accessibility',
                'goals': 'Design inclusive digital experiences', 'pref': 'study_group',
                'skills': ['UI/UX Design', 'HTML/CSS', 'JavaScript', 'Graphic Design'],
                'courses': ['CS301', 'CS201', 'ENG201'],
                'bio': 'Designing technology that works for everyone, especially in Africa.',
            },
            {
                'username': 'hassan_j', 'first': 'Hassan', 'last': 'Juma',
                'email': 'hassan@uni.ac.ke', 'dept': 'Computer Science',
                'year': 1, 'interests': 'programming, algorithms, competitive coding',
                'goals': 'Win programming competitions', 'pref': 'tutoring',
                'skills': ['Python', 'Java', 'C++'],
                'courses': ['CS101', 'MTH101', 'PHY101'],
                'bio': 'Freshman excited about competitive programming and algorithms.',
            },
            {
                'username': 'irene_m', 'first': 'Irene', 'last': 'Mutua',
                'email': 'irene@uni.ac.ke', 'dept': 'Computer Science',
                'year': 4, 'interests': 'cybersecurity, network security, ethical hacking',
                'goals': 'Become a cybersecurity analyst', 'pref': 'study_group',
                'skills': ['Python', 'SQL', 'Project Management', 'Technical Writing'],
                'courses': ['CS402', 'CS303', 'CS301', 'BUS301'],
                'bio': 'Senior student focusing on securing digital infrastructure.',
            },
            {
                'username': 'james_w', 'first': 'James', 'last': 'Wekesa',
                'email': 'james@uni.ac.ke', 'dept': 'Mathematics',
                'year': 3, 'interests': 'data science, machine learning, big data analytics',
                'goals': 'Apply ML to financial data', 'pref': 'project',
                'skills': ['Python', 'Machine Learning', 'Statistics', 'Data Visualization'],
                'courses': ['MTH301', 'CS302', 'CS401', 'MTH201'],
                'bio': 'Using mathematics and ML to understand financial markets.',
            },
            {
                'username': 'karen_l', 'first': 'Karen', 'last': 'Langat',
                'email': 'karen@uni.ac.ke', 'dept': 'Computer Science',
                'year': 2, 'interests': 'mobile development, Android, Kotlin, Flutter',
                'goals': 'Build mobile apps for education', 'pref': 'project',
                'skills': ['Java', 'JavaScript', 'UI/UX Design', 'SQL'],
                'courses': ['CS201', 'CS101', 'ENG201'],
                'bio': 'Building mobile apps to make education accessible in rural areas.',
            },
            {
                'username': 'liam_o', 'first': 'Liam', 'last': 'Otieno',
                'email': 'liam@uni.ac.ke', 'dept': 'Computer Science',
                'year': 3, 'interests': 'machine learning, NLP, chatbots, language models',
                'goals': 'Build NLP tools for African languages', 'pref': 'research',
                'skills': ['Python', 'Machine Learning', 'Data Analysis', 'English Writing'],
                'courses': ['CS302', 'CS401', 'CS301', 'ENG201'],
                'bio': 'Working on NLP models for Swahili and other African languages.',
            },
            # ─── Universal Students (non-tech) ───
            {
                'username': 'mercy_w', 'first': 'Mercy', 'last': 'Wairimu',
                'email': 'mercy@uni.ac.ke', 'dept': 'Nursing',
                'year': 3, 'interests': 'community health, patient care, public health, nutrition',
                'goals': 'Improve rural healthcare delivery', 'pref': 'study_group',
                'skills': ['Patient Care', 'Clinical Assessment', 'Biology', 'Research Methods'],
                'courses': ['NUR201', 'NUR301', 'PSY101'],
                'bio': 'Nursing student committed to improving healthcare in underserved communities.',
            },
            {
                'username': 'peter_n', 'first': 'Peter', 'last': 'Njuguna',
                'email': 'peter@uni.ac.ke', 'dept': 'Psychology',
                'year': 2, 'interests': 'cognitive psychology, mental health, counseling, therapy',
                'goals': 'Study adolescent mental health in East Africa', 'pref': 'research',
                'skills': ['Psychology', 'Research Methods', 'Statistics', 'Academic Writing'],
                'courses': ['PSY101', 'PSY301', 'MTH301', 'EDU301'],
                'bio': 'Exploring the intersection of psychology and mental health in African youth.',
            },
            {
                'username': 'sarah_k', 'first': 'Sarah', 'last': 'Kamau',
                'email': 'sarah@uni.ac.ke', 'dept': 'Economics',
                'year': 3, 'interests': 'microeconomics, development economics, trade policy, econometrics',
                'goals': 'Analyze economic development in Sub-Saharan Africa', 'pref': 'project',
                'skills': ['Economics', 'Statistics', 'Data Analysis', 'Financial Analysis'],
                'courses': ['ECO101', 'ECO301', 'MTH301'],
                'bio': 'Passionate about development economics and policy impact in Africa.',
            },
            {
                'username': 'nancy_m', 'first': 'Nancy', 'last': 'Muthoni',
                'email': 'nancy@uni.ac.ke', 'dept': 'Fine Arts',
                'year': 2, 'interests': 'illustration, digital art, animation, visual storytelling',
                'goals': 'Create African-inspired animated content', 'pref': 'project',
                'skills': ['Drawing & Painting', 'Graphic Design', 'Creative Writing', 'UI/UX Design'],
                'courses': ['ART201', 'ENG201'],
                'bio': 'Artist blending traditional African aesthetics with modern digital media.',
            },
            {
                'username': 'tom_o', 'first': 'Tom', 'last': 'Omondi',
                'email': 'tom@uni.ac.ke', 'dept': 'Law',
                'year': 3, 'interests': 'constitutional law, human rights, legal research, advocacy',
                'goals': 'Advocate for digital privacy rights', 'pref': 'study_group',
                'skills': ['Legal Research', 'Critical Thinking', 'Public Speaking', 'Academic Writing'],
                'courses': ['LAW201', 'PHL201'],
                'bio': 'Law student focused on digital rights and constitutional freedoms.',
            },
            {
                'username': 'ruth_a', 'first': 'Ruth', 'last': 'Adhiambo',
                'email': 'ruth@uni.ac.ke', 'dept': 'Education',
                'year': 4, 'interests': 'pedagogy, educational technology, curriculum design, e-learning',
                'goals': 'Design inclusive e-learning platforms', 'pref': 'project',
                'skills': ['Research Methods', 'Psychology', 'Public Speaking', 'Critical Thinking'],
                'courses': ['EDU301', 'PSY101', 'ENG201'],
                'bio': 'Education major working on making learning accessible through technology.',
            },
        ]

        times = ['morning', 'afternoon', 'evening', 'flexible']
        profiles = []
        for s in students_data:
            user, created = User.objects.get_or_create(
                username=s['username'],
                defaults={
                    'first_name': s['first'],
                    'last_name': s['last'],
                    'email': s['email'],
                }
            )
            if created:
                user.set_password('demo1234')
                user.save()

            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'bio': s['bio'],
                    'department': s['dept'],
                    'year_of_study': s['year'],
                    'interests': s['interests'],
                    'learning_goals': s['goals'],
                    'collaboration_preference': s['pref'],
                    'gpa': round(random.uniform(2.5, 4.0), 2),
                    'available_hours_per_week': random.choice([5, 10, 15, 20]),
                    'preferred_time': random.choice(times),
                }
            )
            profile.skills.set([skills[name] for name in s['skills'] if name in skills])
            profile.courses.set([courses[code] for code in s['courses'] if code in courses])
            profiles.append(profile)

        self.stdout.write(f'  ✅ Created {len(profiles)} student profiles')

        # ─── Resources ───
        resources_data = [
            {
                'title': 'Introduction to Machine Learning with Python',
                'desc': 'Comprehensive guide to building ML models using scikit-learn and Python. Covers supervised, unsupervised, and deep learning.',
                'type': 'textbook', 'tags': 'machine learning, python, scikit-learn, AI',
                'difficulty': 'intermediate', 'rating': 4.7,
                'courses': ['CS401', 'CS302'], 'skills': ['Python', 'Machine Learning'],
            },
            {
                'title': 'Data Structures and Algorithms Masterclass',
                'desc': 'Video lecture series covering arrays, trees, graphs, dynamic programming, and algorithm design.',
                'type': 'video', 'tags': 'algorithms, data structures, coding interviews',
                'difficulty': 'intermediate', 'rating': 4.5,
                'courses': ['CS201'], 'skills': ['Python', 'Java'],
            },
            {
                'title': 'Full-Stack Web Development with Django & React',
                'desc': 'Build complete web applications from scratch using Django REST Framework and React.',
                'type': 'tutorial', 'tags': 'django, react, web development, REST API',
                'difficulty': 'intermediate', 'rating': 4.6,
                'courses': ['CS301', 'CS303'], 'skills': ['Django', 'React', 'JavaScript', 'SQL'],
            },
            {
                'title': 'Linear Algebra for Machine Learning',
                'desc': 'Essential linear algebra concepts for understanding ML: vectors, matrices, eigenvalues, SVD.',
                'type': 'video', 'tags': 'linear algebra, mathematics, ML foundations',
                'difficulty': 'intermediate', 'rating': 4.3,
                'courses': ['MTH201', 'CS401'], 'skills': ['Linear Algebra', 'Machine Learning'],
            },
            {
                'title': 'Probability and Statistics for Data Science',
                'desc': 'Applied probability and statistics for analyzing data and building predictive models.',
                'type': 'textbook', 'tags': 'statistics, probability, data science',
                'difficulty': 'intermediate', 'rating': 4.4,
                'courses': ['MTH301'], 'skills': ['Statistics', 'Probability', 'Data Analysis'],
            },
            {
                'title': 'Python for Beginners: Complete Bootcamp',
                'desc': 'Learn Python from scratch with hands-on exercises, mini projects, and quizzes.',
                'type': 'tutorial', 'tags': 'python, beginner, programming basics',
                'difficulty': 'beginner', 'rating': 4.8,
                'courses': ['CS101'], 'skills': ['Python'],
            },
            {
                'title': 'Research Methods in Natural Language Processing',
                'desc': 'Recent advances in NLP: transformers, BERT, GPT models, and applications in African languages.',
                'type': 'paper', 'tags': 'NLP, transformers, African languages, research',
                'difficulty': 'advanced', 'rating': 4.2,
                'courses': ['CS302', 'CS401'], 'skills': ['Machine Learning', 'Python'],
            },
            {
                'title': 'UI/UX Design Principles for Web Applications',
                'desc': 'Learn user-centered design, wireframing, prototyping, and usability testing.',
                'type': 'tutorial', 'tags': 'UI/UX, design, user experience, accessibility',
                'difficulty': 'beginner', 'rating': 4.5,
                'courses': ['CS301'], 'skills': ['UI/UX Design', 'HTML/CSS'],
            },
            {
                'title': 'Embedded Systems Programming with Arduino',
                'desc': 'Hands-on projects with Arduino: sensors, actuators, IoT applications for agriculture.',
                'type': 'tutorial', 'tags': 'embedded systems, Arduino, IoT, agriculture',
                'difficulty': 'intermediate', 'rating': 4.1,
                'courses': ['ECE301', 'ECE201'], 'skills': ['C++', 'Embedded Systems', 'Circuit Design'],
            },
            {
                'title': 'Database Design and SQL Mastery',
                'desc': 'Relational database design, normalization, advanced SQL queries, and performance tuning.',
                'type': 'textbook', 'tags': 'SQL, databases, normalization, performance',
                'difficulty': 'intermediate', 'rating': 4.4,
                'courses': ['CS303'], 'skills': ['SQL'],
            },
            {
                'title': 'Advanced Java: Design Patterns and Best Practices',
                'desc': 'Enterprise Java patterns: Factory, Observer, Singleton, and clean architecture principles.',
                'type': 'textbook', 'tags': 'java, design patterns, clean code',
                'difficulty': 'advanced', 'rating': 4.3,
                'courses': ['CS301', 'CS201'], 'skills': ['Java'],
            },
            {
                'title': 'Introduction to Cybersecurity',
                'desc': 'Network security fundamentals, ethical hacking basics, and security best practices.',
                'type': 'course_material', 'tags': 'cybersecurity, network security, ethical hacking',
                'difficulty': 'intermediate', 'rating': 4.6,
                'courses': ['CS402'], 'skills': ['Python', 'SQL'],
            },
        ]

        for r in resources_data:
            resource, _ = Resource.objects.get_or_create(
                title=r['title'],
                defaults={
                    'description': r['desc'],
                    'resource_type': r['type'],
                    'tags': r['tags'],
                    'difficulty': r['difficulty'],
                    'rating': r['rating'],
                    'view_count': random.randint(50, 500),
                }
            )
            resource.related_courses.set([courses[c] for c in r['courses'] if c in courses])
            resource.related_skills.set([skills[s] for s in r['skills'] if s in skills])

        self.stdout.write(f'  ✅ Created {len(resources_data)} resources')

        # ─── Collaboration Rooms ───
        rooms_data = [
            ('ML Study Group', 'Weekly ML study sessions', 'study', [0, 5, 9, 11]),
            ('Web Dev Project', 'Full-stack web app collaboration', 'project', [1, 6, 10]),
            ('Stats Tutoring', 'Statistics help and practice', 'tutoring', [2, 9]),
            ('IoT Agriculture Project', 'Smart farming IoT project', 'project', [4, 3]),
            ('Community Health Research', 'Public health collaboration', 'research', [12, 13]),
            ('Arts & Design Hub', 'Creative collaboration space', 'project', [15, 6]),
            ('Study Buddies General', 'Cross-department study support', 'study', [14, 16, 17, 13]),
        ]
        for name, desc, rtype, member_indices in rooms_data:
            room, _ = CollaborationRoom.objects.get_or_create(
                name=name, defaults={'description': desc, 'room_type': rtype}
            )
            for idx in member_indices:
                if idx < len(profiles):
                    room.members.add(profiles[idx])

        self.stdout.write(f'  ✅ Created {len(rooms_data)} collaboration rooms')
        self.stdout.write(self.style.SUCCESS('\n🎉 Database seeded successfully!'))
