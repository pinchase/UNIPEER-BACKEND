"""
UniPeer Models — Student profiles, courses, skills, resources, and matches.
"""

from django.db import models
from django.contrib.auth.models import User
import json


class Skill(models.Model):
    """Academic or technical skill."""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('programming', 'Programming'),
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('language', 'Language'),
        ('design', 'Design'),
        ('business', 'Business'),
        ('engineering', 'Engineering'),
        ('other', 'Other'),
    ], default='other')

    def __str__(self):
        return self.name


class Course(models.Model):
    """University course."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    level = models.IntegerField(choices=[
        (100, 'Year 1'),
        (200, 'Year 2'),
        (300, 'Year 3'),
        (400, 'Year 4'),
        (500, 'Postgraduate'),
    ])

    def __str__(self):
        return f"{self.code} - {self.name}"


class Badge(models.Model):
    """Achievements earned by students."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_emoji = models.CharField(max_length=10)
    requirement_type = models.CharField(max_length=50) # e.g., 'resources', 'matches', 'level'
    requirement_threshold = models.IntegerField()

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    """Extended student profile for ML matching."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField(default=True)
    bio = models.TextField(blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')
    university = models.CharField(max_length=200, default='University of Nairobi')
    department = models.CharField(max_length=200, default='')
    year_of_study = models.IntegerField(default=1)
    gpa = models.FloatField(default=0.0)

    # Gamification
    total_xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    badges = models.ManyToManyField(Badge, blank=True, related_name='students')

    # Academic interests & goals
    interests = models.TextField(blank=True, default='',
                                 help_text='Comma-separated interests')
    learning_goals = models.TextField(blank=True, default='',
                                      help_text='What the student wants to learn')
    collaboration_preference = models.CharField(max_length=20, choices=[
        ('study_group', 'Study Group'),
        ('project', 'Project Partner'),
        ('tutoring', 'Tutoring'),
        ('research', 'Research'),
        ('any', 'Any'),
    ], default='any')

    # Relations
    skills = models.ManyToManyField(Skill, blank=True, related_name='students')
    courses = models.ManyToManyField(Course, blank=True, related_name='students')

    # Availability
    available_hours_per_week = models.IntegerField(default=10)
    preferred_time = models.CharField(max_length=20, choices=[
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('flexible', 'Flexible'),
    ], default='flexible')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"

    def get_feature_text(self):
        """Generate a combined text representation for ML feature extraction."""
        parts = []
        parts.append(self.department)
        parts.append(self.interests)
        parts.append(self.learning_goals)
        parts.append(' '.join(s.name for s in self.skills.all()))
        parts.append(' '.join(c.name for c in self.courses.all()))
        parts.append(self.collaboration_preference)
        return ' '.join(filter(None, parts))


class Resource(models.Model):
    """Academic resource for recommendation."""
    RESOURCE_TYPES = [
        ('textbook', 'Textbook'),
        ('video', 'Video Lecture'),
        ('article', 'Article'),
        ('tutorial', 'Tutorial'),
        ('paper', 'Research Paper'),
        ('tool', 'Tool/Software'),
        ('course_material', 'Course Material'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    url = models.URLField(blank=True, default='')
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    written_content = models.TextField(blank=True, default='')
    tags = models.TextField(blank=True, default='',
                           help_text='Comma-separated tags')
    difficulty = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='intermediate')

    # Relations
    related_courses = models.ManyToManyField(Course, blank=True, related_name='resources')
    related_skills = models.ManyToManyField(Skill, blank=True, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    rating = models.FloatField(default=0.0)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_feature_text(self):
        """Generate text representation for content-based filtering."""
        parts = [
            self.title,
            self.description,
            self.written_content,
            self.tags,
            ' '.join(c.name for c in self.related_courses.all()),
            ' '.join(s.name for s in self.related_skills.all()),
        ]
        return ' '.join(filter(None, parts))


class Match(models.Model):
    """Record of a match between two students."""
    student_a = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='matches_as_a')
    student_b = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='matches_as_b')
    similarity_score = models.FloatField()
    match_reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=[
        ('suggested', 'Suggested'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ], default='suggested')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student_a', 'student_b')
        ordering = ['-similarity_score']

    def __str__(self):
        return f"Match: {self.student_a} ↔ {self.student_b} ({self.similarity_score:.2f})"


class CollaborationRoom(models.Model):
    """A collaboration room for matched students."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    members = models.ManyToManyField(StudentProfile, related_name='rooms')
    room_type = models.CharField(max_length=20, choices=[
        ('direct', 'Direct Message'),
        ('study', 'Study Group'),
        ('project', 'Project'),
        ('tutoring', 'Tutoring'),
    ], default='study')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    """Chat message in a collaboration room."""
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} @ {self.timestamp:%H:%M}"


class EmailVerificationCode(models.Model):
    """Short OTP code for email verification."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=15)

    def __str__(self):
        return f"Code for {self.user.username}"


class Notification(models.Model):
    """User notifications for matches and resources."""
    recipient = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=[
        ('match', 'New Match'),
        ('resource', 'New Resource'),
        ('general', 'General'),
    ], default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient}: {self.message}"
