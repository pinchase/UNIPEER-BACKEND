
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import EmailMultiAlternatives
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Skill, Course, StudentProfile, Resource,
    Match, CollaborationRoom, Message, Notification,
    EmailVerificationCode, PasswordResetCode
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


def sync_suggested_matches_for_profile(profile, top_n=10):
    """Compute and persist suggested matches for a profile, then return computed results."""
    matcher = StudentMatcher()
    all_profiles = StudentProfile.objects.all().select_related('user').prefetch_related('skills', 'courses')
    results = matcher.compute_matches(profile, all_profiles, top_n=top_n)

    for matched_profile, score, reasons in results:
        id_a, id_b = sorted([profile.id, matched_profile.id])
        reason_text = '; '.join(reasons) if isinstance(reasons, list) else str(reasons)

        match, created = Match.objects.get_or_create(
            student_a_id=id_a,
            student_b_id=id_b,
            defaults={
                'similarity_score': score,
                'match_reason': reason_text,
                'status': 'suggested',
            }
        )

        if not created and match.status == 'suggested':
            match.similarity_score = score
            match.match_reason = reason_text
            match.save(update_fields=['similarity_score', 'match_reason'])

    return results


def get_recommended_resources_for_profile(profile, top_n=10):
    """Compute resource recommendations for a profile and return ranked tuples."""
    recommender = ResourceRecommender()
    resources = Resource.objects.all().prefetch_related('related_courses', 'related_skills')
    return recommender.recommend(profile, resources, top_n=top_n)


def get_or_create_direct_room(student_a, student_b):
    """Return the dedicated 1:1 room for two matched students."""
    room = (
        CollaborationRoom.objects
        .filter(members=student_a)
        .filter(members=student_b)
        .annotate(member_count=models.Count('members', distinct=True))
        .filter(member_count=2)
        .order_by('id')
        .first()
    )

    if room:
        updated_fields = []
        desired_name = f"Direct Chat: {student_a.user.username} & {student_b.user.username}"
        desired_description = f"Private conversation between {student_a.user.get_full_name() or student_a.user.username} and {student_b.user.get_full_name() or student_b.user.username}"
        if room.room_type != 'direct':
            room.room_type = 'direct'
            updated_fields.append('room_type')
        if room.name != desired_name:
            room.name = desired_name
            updated_fields.append('name')
        if room.description != desired_description:
            room.description = desired_description
            updated_fields.append('description')
        if updated_fields:
            room.save(update_fields=updated_fields)
        return room, False

    room = CollaborationRoom.objects.create(
        name=f"Direct Chat: {student_a.user.username} & {student_b.user.username}",
        description=f"Private conversation between {student_a.user.get_full_name() or student_a.user.username} and {student_b.user.get_full_name() or student_b.user.username}",
        room_type='direct'
    )
    room.members.add(student_a, student_b)
    return room, True


def broadcast_room_message(message):
    """Push a saved message to any connected websocket listeners for the room."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    serialized_message = MessageSerializer(
        Message.objects.select_related('sender__user', 'room').get(pk=message.pk)
    ).data
    async_to_sync(channel_layer.group_send)(
        f'room_{message.room_id}',
        {
            'type': 'chat.message',
            'message': serialized_message,
        }
    )


def _generate_otp_code():
    import random, string
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(request, user):
    """Generate and send a 6-digit OTP code for email verification."""
    code = _generate_otp_code()
    EmailVerificationCode.objects.update_or_create(
        user=user,
        defaults={'code': code},
    )

    name = user.first_name or user.username
    subject = "Your UniPeer verification code"

    # ── Plain-text fallback ──────────────────────────────
    plain_message = (
        f"Hi {name},\n\n"
        f"Your UniPeer email verification code is:\n\n    {code}\n\n"
        "This code expires in 15 minutes.\n\n"
        "If you did not create a UniPeer account, you can safely ignore this email.\n\n"
        "— The UniPeer Team 🎓"
    )

    # ── HTML email ───────────────────────────────────────
    code_digits = ''.join(
        f'<span style="display:inline-block;width:44px;height:52px;line-height:52px;'
        f'text-align:center;font-size:28px;font-weight:700;color:#ffffff;'
        f'background:#4f46e5;border-radius:10px;margin:0 4px;">{d}</span>'
        for d in code
    )
    html_message = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f0e17;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0e17;padding:40px 0;">
    <tr><td align="center">
      <table width="540" cellpadding="0" cellspacing="0" style="background:#1a1825;border-radius:20px;overflow:hidden;max-width:540px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:36px 40px;text-align:center;">
            <div style="font-size:40px;margin-bottom:8px;">🎓</div>
            <div style="color:#ffffff;font-size:26px;font-weight:800;letter-spacing:-0.5px;">UniPeer</div>
            <div style="color:rgba(255,255,255,0.75);font-size:13px;margin-top:4px;">Your Academic Network</div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">
            <p style="color:#e2e0f0;font-size:17px;margin:0 0 8px 0;">Hi <strong>{name}</strong> 👋</p>
            <p style="color:#a09cbf;font-size:15px;margin:0 0 32px 0;">
              Use the code below to verify your email address. It expires in <strong style="color:#a78bfa;">15&nbsp;minutes</strong>.
            </p>

            <!-- OTP digits -->
            <div style="text-align:center;margin:0 0 32px 0;letter-spacing:2px;">
              {code_digits}
            </div>

            <p style="color:#6b6886;font-size:13px;text-align:center;margin:0 0 32px 0;">
              Enter this code on the verification page to activate your account.
            </p>

            <hr style="border:none;border-top:1px solid #2d2a40;margin:0 0 28px 0;">

            <p style="color:#4a4761;font-size:12px;margin:0;text-align:center;line-height:1.6;">
              Didn't sign up for UniPeer? You can safely ignore this email.<br>
              This code cannot be used to access your account without your password.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#13111f;padding:20px 40px;text-align:center;">
            <p style="color:#4a4761;font-size:12px;margin:0;">
              © 2026 UniPeer · Built for students, by students 🎓
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    email_msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)


def send_password_reset_email(request, user, code):
    """Email a one-time reset code and instructions to the requester."""
    name = user.first_name or user.username
    subject = "Reset your UniPeer password"

    plain_message = (
        f"Hi {name},\n\n"
        "A password reset was requested for your UniPeer account. "
        f"Use the code below to set a new password. It expires in 15 minutes.\n\n"
        f"Password reset code: {code}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "— UniPeer Team 🎓"
    )

    code_digits = ''.join(
        f'<span style="display:inline-block;width:44px;height:52px;line-height:52px;'
        f'text-align:center;font-size:28px;font-weight:700;color:#ffffff;'
        f'background:#dc2626;border-radius:10px;margin:0 4px;">{d}</span>'
        for d in code
    )

    html_message = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f0e17;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0e17;padding:40px 0;">
    <tr><td align="center">
      <table width="540" cellpadding="0" cellspacing="0" style="background:#1a1825;border-radius:20px;overflow:hidden;max-width:540px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:36px 40px;text-align:center;">
            <div style="font-size:40px;margin-bottom:8px;">🎓</div>
            <div style="color:#ffffff;font-size:26px;font-weight:800;letter-spacing:-0.5px;">UniPeer</div>
            <div style="color:rgba(255,255,255,0.75);font-size:13px;margin-top:4px;">Secure Your Account</div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">
            <p style="color:#e2e0f0;font-size:17px;margin:0 0 8px 0;">Hi <strong>{name}</strong>,</p>
            <p style="color:#a09cbf;font-size:15px;margin:0 0 32px 0;">
              You requested to reset your UniPeer password. Enter the code below on the password reset
              page and choose a new password. The code expires in <strong style="color:#f87171;">15 minutes</strong>.
            </p>

            <!-- OTP digits -->
            <div style="text-align:center;margin:0 0 32px 0;letter-spacing:2px;">
              {code_digits}
            </div>

            <p style="color:#6b6886;font-size:13px;text-align:center;margin:0 0 32px 0;">
              Visit <a href="https://unipeer-frontend.vercel.app/reset-password.html" style="color:#a78bfa;">UniPeer Password Reset</a> and paste this code to finish.
            </p>

            <hr style="border:none;border-top:1px solid #2d2a40;margin:0 0 28px 0;">

            <p style="color:#4a4761;font-size:12px;margin:0;text-align:center;line-height:1.6;">
              If you did not request this, please ignore this email. The code cannot be used without your password.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#13111f;padding:20px 40px;text-align:center;">
            <p style="color:#4a4761;font-size:12px;margin:0;">
              © 2026 UniPeer · Built for students, by students 🎓
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    email_msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)


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
        results = sync_suggested_matches_for_profile(profile, top_n=10)

        match_data = [
            {'profile': StudentProfileSerializer(p).data, 'score': round(s, 3), 'reasons': r}
            for p, s, r in results
        ]
        return Response(match_data)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get resource recommendations for a specific student."""
        profile = self.get_object()
        results = get_recommended_resources_for_profile(profile, top_n=10)

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
        match_results = sync_suggested_matches_for_profile(profile, top_n=5)

        # Compute resource recommendations
        rec_results = get_recommended_resources_for_profile(profile, top_n=5)

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
        recommended_for_profile_id = self.request.query_params.get('recommended_for_profile_id')
        if recommended_for_profile_id:
            try:
                profile = StudentProfile.objects.get(id=int(recommended_for_profile_id))
            except (StudentProfile.DoesNotExist, TypeError, ValueError):
                return queryset.none()

            top_n_param = self.request.query_params.get('top_n', 10)
            try:
                top_n = max(1, min(int(top_n_param), 50))
            except (TypeError, ValueError):
                top_n = 10

            recommended = get_recommended_resources_for_profile(profile, top_n=top_n)
            recommended_ids = [resource.id for resource, _ in recommended]
            if not recommended_ids:
                return queryset.none()

            order_case = models.Case(
                *[models.When(id=resource_id, then=position) for position, resource_id in enumerate(recommended_ids)],
                output_field=models.IntegerField(),
            )
            return queryset.filter(id__in=recommended_ids).order_by(order_case)

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
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Filter matches where the student is either a or b
        profile_id = self.request.query_params.get('profile_id')
        if profile_id:
            queryset = Match.objects.filter(
                models.Q(student_a_id=profile_id) | models.Q(student_b_id=profile_id)
            )
            if not queryset.exists():
                profile = get_object_or_404(StudentProfile, id=profile_id)
                sync_suggested_matches_for_profile(profile, top_n=10)
                queryset = Match.objects.filter(
                    models.Q(student_a_id=profile_id) | models.Q(student_b_id=profile_id)
                )
            return queryset
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

        if not created:
            updated_fields = []
            if match.status != 'accepted':
                match.status = 'accepted'
                updated_fields.append('status')
            if str(match.match_reason or '') != str(match_reason or ''):
                match.match_reason = match_reason
                updated_fields.append('match_reason')
            try:
                similarity_score_value = float(similarity_score)
            except (TypeError, ValueError):
                similarity_score_value = match.similarity_score
            if match.similarity_score != similarity_score_value:
                match.similarity_score = similarity_score_value
                updated_fields.append('similarity_score')
            if updated_fields:
                match.save(update_fields=updated_fields)

        room, room_created = get_or_create_direct_room(student_a, student_b)

        if created:
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

        payload = MatchSerializer(match).data
        payload['room_id'] = room.id
        payload['room_created'] = room_created
        payload['room'] = CollaborationRoomSerializer(room).data
        return Response(
            payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CollaborationRoomViewSet(viewsets.ModelViewSet):
    queryset = CollaborationRoom.objects.all().prefetch_related('members')
    serializer_class = CollaborationRoomSerializer
    permission_classes = [AllowAny]

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
        if not room.members.filter(id=profile.id).exists():
            return Response({'error': 'Sender must belong to the room'}, status=403)

        msg = Message.objects.create(room=room, sender=profile, content=content)
        broadcast_room_message(msg)
        return Response(MessageSerializer(msg).data, status=201)


# ─── Registration ──────────────────────────────────────

class RegisterView(APIView):
    """Register a new student and create their profile."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentProfileCreateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            profile.email_verified = False
            profile.save(update_fields=['email_verified'])
            try:
                send_verification_email(request, profile.user)
            except Exception:
                return Response(
                    {
                        'error': 'Account created, but verification email could not be sent. Please request resend.'
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            return Response(
                {
                    'profile': StudentProfileSerializer(profile).data,
                    'email': profile.user.email,
                    'message': 'Registration successful. Check your email for your verification code.',
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticate a student via email and password."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password required'}, status=400)

        candidates = list(User.objects.filter(email__iexact=email).order_by('-id'))
        if not candidates:
            return Response({'error': 'User not found'}, status=404)

        authenticated_user = None
        for candidate in candidates:
            matched = authenticate(username=candidate.username, password=password)
            if matched:
                authenticated_user = matched
                break

        if authenticated_user:
            if not hasattr(authenticated_user, 'profile'):
                return Response({'error': 'Profile not found for this account.'}, status=404)

            if not authenticated_user.profile.email_verified:
                return Response(
                    {'error': 'Email not verified. Please verify your email before logging in.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            refresh = RefreshToken.for_user(authenticated_user)
            return Response({
                'profile': StudentProfileSerializer(authenticated_user.profile).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
        return Response({'error': 'Invalid credentials'}, status=401)


class VerifyEmailView(APIView):
    """Verify user email using a 6-digit OTP code submitted from the frontend."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        raw_code = (request.data.get('code') or '').strip()
        code = ''.join(ch for ch in raw_code if ch.isdigit())

        if not email or not code:
            return Response({'error': 'Email and code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(code) != 6:
            return Response({'error': 'Code must be 6 digits.'}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(email__iexact=email).order_by('-id')
        if not users.exists():
            return Response({'error': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

        otp = (
            EmailVerificationCode.objects
            .filter(user__email__iexact=email, code=code)
            .select_related('user__profile')
            .order_by('-created_at')
            .first()
        )

        if otp:
            if otp.is_expired():
                return Response({'error': 'Code has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

            user = otp.user
            if not hasattr(user, 'profile'):
                return Response({'error': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

            if user.profile.email_verified:
                otp.delete()
                return Response({'message': 'Email is already verified. You can log in.'})

            user.profile.email_verified = True
            user.profile.save(update_fields=['email_verified'])

            # Keep one-time semantics strict if legacy duplicate-email records exist.
            EmailVerificationCode.objects.filter(user__email__iexact=email).delete()

            return Response({'message': 'Email verified successfully. You can now log in.'})

        latest_otp = (
            EmailVerificationCode.objects
            .filter(user__email__iexact=email)
            .order_by('-created_at')
            .first()
        )

        if not latest_otp:
            any_verified = users.filter(profile__email_verified=True).exists()
            if any_verified:
                return Response({'message': 'Email is already verified. You can log in.'})
            return Response({'error': 'No verification code found. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        if latest_otp.is_expired():
            return Response({'error': 'Code has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Incorrect code. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """Resend email verification link for an existing unverified account."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        users = list(User.objects.filter(email__iexact=email).order_by('-id'))
        if not users:
            return Response({'message': 'If the account exists, a verification email has been sent.'})

        user = None
        for candidate in users:
            if hasattr(candidate, 'profile') and not candidate.profile.email_verified:
                user = candidate
                break

        if not user:
            return Response({'message': 'Email is already verified.'})

        try:
            send_verification_email(request, user)
        except Exception:
            return Response(
                {'error': 'Could not send verification email right now. Try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'message': 'A new 6-digit code has been sent to your email.'})


class PasswordResetRequestView(APIView):
    """Send a one-time reset code to the user's email."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).order_by('-id').first()
        if not user:
            return Response({'message': 'If an account exists, a password reset email has been sent.'})

        code = _generate_otp_code()
        PasswordResetCode.objects.update_or_create(
            user=user,
            defaults={'code': code}
        )

        try:
            send_password_reset_email(request, user, code)
        except Exception:
            return Response(
                {'error': 'Could not send password reset email. Try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({'message': 'If an account exists, a password reset email has been sent.'})


class PasswordResetConfirmView(APIView):
    """Confirm a reset code and replace the user's password."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        code = (request.data.get('code') or '').strip()
        password = request.data.get('password') or ''

        if not email or not code or not password:
            return Response({'error': 'Email, code, and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(code) != 6 or not code.isdigit():
            return Response({'error': 'Code must be 6 digits.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).order_by('-id').first()
        if not user:
            return Response({'error': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            reset = user.password_reset_code
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Reset code not found. Request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        if reset.is_expired():
            reset.delete()
            return Response({'error': 'Code has expired. Request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        if reset.code != code:
            return Response({'error': 'Incorrect code.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password, user)
        except ValidationError as exc:
            return Response({'error': exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        reset.delete()

        return Response({'message': 'Password reset successful. You can now log in.'})


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
