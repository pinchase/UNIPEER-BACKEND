from django.contrib import admin
from .models import (
    Skill, Course, StudentProfile, Resource,
    Match, CollaborationRoom, Message
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'level']
    list_filter = ['department', 'level']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'year_of_study', 'collaboration_preference']
    list_filter = ['department', 'year_of_study', 'collaboration_preference']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'difficulty', 'rating']
    list_filter = ['resource_type', 'difficulty']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['student_a', 'student_b', 'similarity_score', 'status']
    list_filter = ['status']


@admin.register(CollaborationRoom)
class CollaborationRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'is_active']
    list_filter = ['room_type', 'is_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'timestamp']
