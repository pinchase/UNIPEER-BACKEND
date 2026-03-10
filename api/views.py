"""
UniPeer API Views — Endpoints for profiles, matching, resources, and collaboration.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import models

from .models import (
    Skill, Course, StudentProfile, Resource,
    Match, CollaborationRoom, Message, Notification
)
from .serializers import (
    SkillSerializer, CourseSerializer, StudentProfileSerializer,
    StudentProfileCreateSerializer, ResourceSerializer,
    MatchSerializer, MatchResultSerializer,
    ResourceRecommendationSerializer, CollaborationRoomSerializer,
    MessageSerializer, DashboardSerializer, NotificationSerializer
)
from .ml_engine import StudentMatcher, ResourceRecommender
from .throttles import NotificationAnonThrottle, NotificationBurstThrottle, NotificationUserThrottle


# ─── Viewsets ──────────────────────────────────────────

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all().select_related('user').prefetch_related('skills', 'courses')
    serializer_class = StudentProfileSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Get ML-computed matches for a specific student."""
        profile = self.get_object()
        matcher = StudentMatcher()
        all_profiles = StudentProfile.objects.all().select_related('user').prefetch_related('skills', 'courses')
        results = matcher.compute_matches(profile, all_profiles, top_n=10)

        match_data = [
            {'profile': StudentProfileSerializer(p).data, 'score': round(s, 3), 'reasons': r}
            for p, s, r in results
        ]
        return Response(match_data)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get resource recommendations for a specific student."""
        profile = self.get_object()
        recommender = ResourceRecommender()
        resources = Resource.objects.all().prefetch_related('related_courses', 'related_skills')
        results = recommender.recommend(profile, resources, top_n=10)

        rec_data = [
            {'resource': ResourceSerializer(r).data, 'relevance_score': round(s, 3)}
            for r, s in results
        ]
        return Response(rec_data)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get dashboard data for a student."""
        profile = self.get_object()

        # Compute matches
        matcher = StudentMatcher()
        all_profiles = StudentProfile.objects.all().select_related('user').prefetch_related('skills', 'courses')
        match_results = matcher.compute_matches(profile, all_profiles, top_n=5)

        # Compute resource recommendations
        recommender = ResourceRecommender()
        resources = Resource.objects.all().prefetch_related('related_courses', 'related_skills')
        rec_results = recommender.recommend(profile, resources, top_n=5)

        # Count stats
        total_matches = Match.objects.filter(
            student_a=profile
        ).count() + Match.objects.filter(
            student_b=profile
        ).count()
        active_rooms = profile.rooms.filter(is_active=True).count()

        data = {
            'profile': StudentProfileSerializer(profile).data,
            'total_matches': total_matches,
            'active_rooms': active_rooms,
            'recommended_resources_count': len(rec_results),
            'uploaded_resources_count': Resource.objects.filter(uploaded_by=profile.user).count(),
            'top_matches': [
                {'profile': StudentProfileSerializer(p).data, 'score': round(s, 3), 'reasons': r}
                for p, s, r in match_results
            ],
            'recent_resources': [
                {'resource': ResourceSerializer(r).data, 'relevance_score': round(s, 3)}
                for r, s in rec_results
            ],
        }
        return Response(data)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all().prefetch_related('related_courses', 'related_skills')
    serializer_class = ResourceSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        queryset = Resource.objects.all().prefetch_related('related_courses', 'related_skills')
        uploader_profile_id = self.request.query_params.get('uploader_profile_id')
        if uploader_profile_id:
            queryset = queryset.filter(uploaded_by__profile__id=uploader_profile_id)
        return queryset

    def perform_create(self, serializer):
        # In this demo app, we might not have a logged-in user via session.
        # We check for an 'uploader_id' in the form data (which corresponds to StudentProfile.id)
        uploader_profile_id = self.request.data.get('uploader_id')
        user = self.request.user
        
        if uploader_profile_id:
            try:
                profile = StudentProfile.objects.get(id=uploader_profile_id)
                user = profile.user
            except (StudentProfile.DoesNotExist, ValueError, TypeError):
                pass
                
        # If we found a valid user, assign it
        if user and user.is_authenticated:
            serializer.save(uploaded_by=user)
        else:
            serializer.save()


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().select_related('recipient', 'recipient__user')
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [NotificationBurstThrottle, NotificationUserThrottle, NotificationAnonThrottle]

    def get_queryset(self):
        queryset = Notification.objects.all().select_related('recipient', 'recipient__user')
        recipient_id = self.request.query_params.get('recipient_id')
        if not recipient_id:
            return queryset.none()

        try:
            recipient_id = int(recipient_id)
        except (TypeError, ValueError):
            return queryset.none()

        return queryset.filter(recipient_id=recipient_id)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def get_queryset(self):
        # Filter matches where the student is either a or b
        profile_id = self.request.query_params.get('profile_id')
        if profile_id:
            return Match.objects.filter(
                models.Q(student_a_id=profile_id) | models.Q(student_b_id=profile_id)
            )
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        student_a_id = request.data.get('student_a')
        student_b_id = request.data.get('student_b')
        similarity_score = request.data.get('similarity_score', 0.0)
        match_reason = request.data.get('match_reason', 'Connecting via UniPeer')

        if not student_a_id or not student_b_id:
            return Response({'error': 'Both students are required'}, status=400)

        try:
            student_a_id = int(student_a_id)
            student_b_id = int(student_b_id)
        except (TypeError, ValueError):
            return Response({'error': 'student_a and student_b must be valid IDs'}, status=400)

        if student_a_id == student_b_id:
            return Response({'error': 'A student cannot be matched with themselves'}, status=400)

        # Ensure order to prevent duplicates (student_a < student_b)
        id_a, id_b = sorted([student_a_id, student_b_id])
        
        student_a = get_object_or_404(StudentProfile, id=id_a)
        student_b = get_object_or_404(StudentProfile, id=id_b)

        match, created = Match.objects.get_or_create(
            student_a=student_a,
            student_b=student_b,
            defaults={
                'similarity_score': similarity_score,
                'match_reason': match_reason,
                'status': 'accepted'
            }
        )

        if created:
            # Create a collaboration room for them
            room_name = f"Chat: {student_a.user.username} & {student_b.user.username}"
            room = CollaborationRoom.objects.create(
                name=room_name,
                description=f"Collaboration between {student_a.user.get_full_name()} and {student_b.user.get_full_name()}",
                room_type='study'
            )
            room.members.add(student_a, student_b)

            # Create notifications
            Notification.objects.create(
                recipient=student_b,
                message=f"New match with {student_a.user.get_full_name()}! You can now collaborate.",
                notification_type='match'
            )
            Notification.objects.create(
                recipient=student_a,
                message=f"New match with {student_b.user.get_full_name()}! You can now collaborate.",
                notification_type='match'
            )

        return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)


class CollaborationRoomViewSet(viewsets.ModelViewSet):
    queryset = CollaborationRoom.objects.all().prefetch_related('members')
    serializer_class = CollaborationRoomSerializer

    def get_queryset(self):
        queryset = CollaborationRoom.objects.all().prefetch_related('members')
        profile_id = self.request.query_params.get('profile_id')
        if profile_id:
            queryset = queryset.filter(members__id=profile_id)
        return queryset

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all().select_related('sender__user')
        return Response(MessageSerializer(messages, many=True).data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        room = self.get_object()
        profile_id = request.data.get('sender_id')
        content = request.data.get('content', '')

        if not profile_id or not content:
            return Response({'error': 'sender_id and content required'}, status=400)

        try:
            profile_id = int(profile_id)
        except (TypeError, ValueError):
            return Response({'error': 'sender_id must be a valid ID'}, status=400)

        profile = get_object_or_404(StudentProfile, id=profile_id)
        msg = Message.objects.create(room=room, sender=profile, content=content)
        return Response(MessageSerializer(msg).data, status=201)


# ─── Registration ──────────────────────────────────────

class RegisterView(APIView):
    """Register a new student and create their profile."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentProfileCreateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(
                StudentProfileSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticate a student via email and password."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password required'}, status=400)

        user = User.objects.filter(email=email).order_by('id').first()
        if not user:
            return Response({'error': 'User not found'}, status=404)

        user = authenticate(username=user.username, password=password)
        if user:
            return Response(StudentProfileSerializer(user.profile).data)
        return Response({'error': 'Invalid credentials'}, status=401)


# ─── Stats ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def platform_stats(request):
    """General platform statistics - public endpoint."""
    return Response({
        'total_students': StudentProfile.objects.count(),
        'total_resources': Resource.objects.count(),
        'total_courses': Course.objects.count(),
        'total_skills': Skill.objects.count(),
        'total_matches': Match.objects.count(),
        'active_rooms': CollaborationRoom.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def keep_alive(request):
    """Lightweight health endpoint for uptime monitors."""
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([AllowAny])
def whoami(request):
    """Return basic authentication context for debugging auth flows."""
    user = request.user
    if not user or not user.is_authenticated:
        return Response({'authenticated': False, 'user': None})
    return Response({
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
    })
