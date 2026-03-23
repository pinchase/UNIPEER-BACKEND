from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Skill, Course, StudentProfile, Resource,
    Match, CollaborationRoom, Message, Notification, Badge
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    badges = BadgeSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), many=True, write_only=True, source='skills', required=False
    )
    course_ids = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), many=True, write_only=True, source='courses', required=False
    )
    skill_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    course_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'full_name', 'display_name', 'name', 'email_verified', 'bio', 'avatar_url',
            'university', 'department', 'year_of_study', 'gpa',
            'interests', 'learning_goals', 'collaboration_preference',
            'skills', 'courses', 'skill_ids', 'course_ids', 'skill_names', 'course_names',
            'first_name', 'last_name', 'email',
            'available_hours_per_week', 'preferred_time',
            'total_xp', 'current_level', 'badges',
            'created_at', 'updated_at', 'match_score',
        ]

    def _can_view_personal(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user == getattr(obj, 'user', None):
            return True
        return bool(getattr(obj, 'show_personal_info', False))

    def get_full_name(self, obj):
        if self._can_view_personal(obj):
            return obj.user.get_full_name() or obj.user.username
        return None

    def get_display_name(self, obj):
        if self._can_view_personal(obj):
            return obj.user.get_full_name() or obj.user.username
        return None

    def get_name(self, obj):
        if self._can_view_personal(obj):
            return obj.user.get_full_name() or obj.user.username
        return None

    def get_match_score(self, obj):
        # match_score may be attached to object by view as attribute or passed via context
        score = getattr(obj, 'match_score', None)
        if score is None:
            score = self.context.get('match_score')
        return round(score, 3) if score is not None else None

    def update(self, instance, validated_data):
        user = instance.user
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        email = validated_data.pop('email', None)
        skill_names = validated_data.pop('skill_names', None)
        course_names = validated_data.pop('course_names', None)
        skills = validated_data.pop('skills', None)
        courses = validated_data.pop('courses', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        user_dirty = False
        if first_name is not None:
            user.first_name = first_name
            user_dirty = True
        if last_name is not None:
            user.last_name = last_name
            user_dirty = True
        if email is not None:
            user.email = email.strip().lower()
            user_dirty = True
        if user_dirty:
            user.save()

        if skills is not None or skill_names is not None:
            normalized_skills = list(skills) if skills is not None else []
            for raw_name in skill_names or []:
                name = raw_name.strip()
                if not name:
                    continue
                skill, _ = Skill.objects.get_or_create(name=name)
                normalized_skills.append(skill)
            instance.skills.set(normalized_skills)

        if courses is not None or course_names is not None:
            normalized_courses = list(courses) if courses is not None else []
            for raw_name in course_names or []:
                name = raw_name.strip()
                if not name:
                    continue
                if ' - ' in name:
                    code, cname = name.split(' - ', 1)
                    course, _ = Course.objects.get_or_create(
                        code=code.strip(),
                        defaults={
                            'name': cname.strip(),
                            'department': instance.department,
                            'level': 100,
                        },
                    )
                else:
                    course, _ = Course.objects.get_or_create(
                        code=name[:20],
                        defaults={
                            'name': name,
                            'department': instance.department,
                            'level': 100,
                        },
                    )
                normalized_courses.append(course)
            instance.courses.set(normalized_courses)

        return instance


class StudentProfileCreateSerializer(serializers.Serializer):
    """Serializer for creating a profile + user in one request."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    bio = serializers.CharField(required=False, default='', allow_blank=True)
    university = serializers.CharField(required=False, default='University of Nairobi', allow_blank=True)
    department = serializers.CharField(required=False, default='', allow_blank=True)
    year_of_study = serializers.IntegerField(required=False, default=1)
    interests = serializers.CharField(required=False, default='', allow_blank=True)
    learning_goals = serializers.CharField(required=False, default='', allow_blank=True)
    collaboration_preference = serializers.ChoiceField(
        choices=['study_group', 'project', 'tutoring', 'research', 'any'],
        required=False, default='any'
    )
    available_hours_per_week = serializers.IntegerField(required=False, default=10)
    preferred_time = serializers.ChoiceField(
        choices=['morning', 'afternoon', 'evening', 'flexible'],
        required=False, default='flexible'
    )
    skill_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    course_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    skill_names = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    course_names = serializers.ListField(child=serializers.CharField(), required=False, default=[])

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        normalized = (value or '').strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                "An account with this email already exists. Please log in or verify your email."
            )
        return normalized

    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        course_ids = validated_data.pop('course_ids', [])
        skill_names = validated_data.pop('skill_names', [])
        course_names = validated_data.pop('course_names', [])

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
        )

        profile = StudentProfile.objects.create(
            user=user,
            bio=validated_data.get('bio', ''),
            university=validated_data.get('university', 'University of Nairobi'),
            department=validated_data.get('department', ''),
            year_of_study=validated_data.get('year_of_study', 1),
            interests=validated_data.get('interests', ''),
            learning_goals=validated_data.get('learning_goals', ''),
            collaboration_preference=validated_data.get('collaboration_preference', 'any'),
            available_hours_per_week=validated_data.get('available_hours_per_week', 10),
            preferred_time=validated_data.get('preferred_time', 'flexible'),
        )

        # Handle IDs first
        if skill_ids:
            profile.skills.add(*Skill.objects.filter(id__in=skill_ids))
        if course_ids:
            profile.courses.add(*Course.objects.filter(id__in=course_ids))

        # Handle names (create if not exists)
        for name in skill_names:
            skill, _ = Skill.objects.get_or_create(name=name.strip())
            profile.skills.add(skill)

        for name in course_names:
            # Check if name looks like "CODE - NAME"
            if " - " in name:
                code, cname = name.split(" - ", 1)
                course, _ = Course.objects.get_or_create(
                    code=code.strip(),
                    defaults={'name': cname.strip(), 'department': profile.department, 'level': 100}
                )
            else:
                # Fallback to name as code/name
                course, _ = Course.objects.get_or_create(
                    code=name.strip()[:20],
                    defaults={'name': name.strip(), 'department': profile.department, 'level': 100}
                )
            profile.courses.add(course)

        return profile


class ResourceSerializer(serializers.ModelSerializer):
    related_courses = CourseSerializer(many=True, read_only=True)
    related_skills = SkillSerializer(many=True, read_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        file_obj = attrs.get('file')
        url = attrs.get('url', '')
        written_content = attrs.get('written_content', '')

        if self.instance is not None:
            file_obj = file_obj or self.instance.file
            url = url or self.instance.url
            written_content = written_content or self.instance.written_content

        if request and not file_obj:
            file_obj = request.FILES.get('file')

        has_file = bool(file_obj)
        has_url = bool((url or '').strip())
        has_written = bool((written_content or '').strip())

        if not (has_file or has_url or has_written):
            raise serializers.ValidationError('Provide at least one resource content: file, URL, or written_content.')

        return attrs

    class Meta:
        model = Resource
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer):
    student_a = StudentProfileSerializer(read_only=True)
    student_b = StudentProfileSerializer(read_only=True)

    class Meta:
        model = Match
        fields = '__all__'


class MatchResultSerializer(serializers.Serializer):
    """Serializer for match results from the ML engine."""
    profile = StudentProfileSerializer()
    score = serializers.FloatField()
    reasons = serializers.CharField()


class ResourceRecommendationSerializer(serializers.Serializer):
    """Serializer for resource recommendation results."""
    resource = ResourceSerializer()
    relevance_score = serializers.FloatField()


class CollaborationRoomSerializer(serializers.ModelSerializer):
    members = StudentProfileSerializer(many=True, read_only=True)

    class Meta:
        model = CollaborationRoom
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender = StudentProfileSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'


class DashboardSerializer(serializers.Serializer):
    """Serializer for the student dashboard overview."""
    profile = StudentProfileSerializer()
    total_matches = serializers.IntegerField()
    active_rooms = serializers.IntegerField()
    recommended_resources_count = serializers.IntegerField()
    top_matches = MatchResultSerializer(many=True)
    recent_resources = ResourceRecommendationSerializer(many=True)
