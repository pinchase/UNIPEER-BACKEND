import asyncio

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CollaborationRoom, Match, MatchInvite, Message, Notification, Resource, Skill, StudentProfile
from .ws_auth import CookieJWTAuthMiddleware


class MatchInviteAPITests(APITestCase):
    def setUp(self):
        self.sender_user = User.objects.create_user(
            username='sender',
            password='secret123',
            first_name='Send',
            last_name='Er',
            email='sender@example.com',
        )
        self.recipient_user = User.objects.create_user(
            username='recipient',
            password='secret123',
            first_name='Rec',
            last_name='Ipient',
            email='recipient@example.com',
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='secret123',
            first_name='O',
            last_name='Ther',
            email='other@example.com',
        )

        self.sender_profile = StudentProfile.objects.create(user=self.sender_user, department='CS', year_of_study=2)
        self.recipient_profile = StudentProfile.objects.create(user=self.recipient_user, department='Math', year_of_study=3)
        self.other_profile = StudentProfile.objects.create(user=self.other_user, department='Physics', year_of_study=1)

    def test_authenticated_user_can_create_invite(self):
        self.client.force_authenticate(user=self.sender_user)

        response = self.client.post(
            '/api/invites/',
            {'recipient_id': self.recipient_profile.id, 'message': 'Want to collaborate?'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite = MatchInvite.objects.get()
        self.assertEqual(invite.sender, self.sender_profile)
        self.assertEqual(invite.recipient, self.recipient_profile)
        self.assertEqual(invite.status, MatchInvite.STATUS_PENDING)

    def test_pending_invite_cannot_be_duplicated(self):
        MatchInvite.objects.create(sender=self.sender_profile, recipient=self.recipient_profile, message='First')
        self.client.force_authenticate(user=self.sender_user)

        response = self.client.post(
            '/api/invites/',
            {'recipient_id': self.recipient_profile.id, 'message': 'Second'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MatchInvite.objects.count(), 1)

    def test_recipient_can_accept_invite_and_create_match_and_room(self):
        invite = MatchInvite.objects.create(sender=self.sender_profile, recipient=self.recipient_profile, message='Hello')
        self.client.force_authenticate(user=self.recipient_user)

        response = self.client.post(f'/api/invites/{invite.id}/accept/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invite.refresh_from_db()
        self.assertEqual(invite.status, MatchInvite.STATUS_ACCEPTED)
        self.assertIsNotNone(invite.related_match)
        self.assertEqual(invite.related_match.status, 'accepted')

        room = CollaborationRoom.objects.get(room_type='direct')
        self.assertEqual(room.members.count(), 2)
        self.assertTrue(room.members.filter(id=self.sender_profile.id).exists())
        self.assertTrue(room.members.filter(id=self.recipient_profile.id).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.sender_profile, notification_type='match').exists())

    def test_only_recipient_can_accept_invite(self):
        invite = MatchInvite.objects.create(sender=self.sender_profile, recipient=self.recipient_profile, message='Hello')
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(f'/api/invites/{invite.id}/accept/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        invite.refresh_from_db()
        self.assertEqual(invite.status, MatchInvite.STATUS_PENDING)

    def test_recipient_can_decline_invite(self):
        invite = MatchInvite.objects.create(sender=self.sender_profile, recipient=self.recipient_profile, message='Hello')
        self.client.force_authenticate(user=self.recipient_user)

        response = self.client.post(f'/api/invites/{invite.id}/decline/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invite.refresh_from_db()
        self.assertEqual(invite.status, MatchInvite.STATUS_DECLINED)
        self.assertTrue(Notification.objects.filter(recipient=self.sender_profile, notification_type='match').exists())

    def test_invite_list_is_scoped_to_authenticated_profile(self):
        own_invite = MatchInvite.objects.create(sender=self.sender_profile, recipient=self.recipient_profile, message='Scoped')
        MatchInvite.objects.create(sender=self.other_profile, recipient=self.recipient_profile, message='Other')
        self.client.force_authenticate(user=self.sender_user)

        response = self.client.get('/api/invites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertEqual(returned_ids, {own_invite.id})

    def test_existing_match_blocks_new_invite(self):
        student_a, student_b = sorted([self.sender_profile, self.recipient_profile], key=lambda profile: profile.id)
        Match.objects.create(
            student_a=student_a,
            student_b=student_b,
            similarity_score=0.8,
            match_reason='Already matched',
            status='accepted',
        )
        self.client.force_authenticate(user=self.sender_user)

        response = self.client.post(
            '/api/invites/',
            {'recipient_id': self.recipient_profile.id, 'message': 'Should fail'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MatchInvite.objects.count(), 0)


class AuthCookieAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='auth-user',
            password='secret123',
            email='auth@example.com',
        )
        self.profile = StudentProfile.objects.create(user=self.user, department='CS', year_of_study=2, email_verified=True)

    def test_login_sets_http_only_cookies_and_refresh_rotates(self):
        response = self.client.post('/api/login/', {'email': 'auth@example.com', 'password': 'secret123'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unipeer_access', response.cookies)
        self.assertIn('unipeer_refresh', response.cookies)
        self.assertTrue(response.cookies['unipeer_access']['httponly'])
        self.assertTrue(response.cookies['unipeer_refresh']['httponly'])

        refresh_cookie = response.cookies['unipeer_refresh'].value
        refresh_response = self.client.post('/api/token/refresh/', format='json')

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('unipeer_access', refresh_response.cookies)
        self.assertIn('unipeer_refresh', refresh_response.cookies)
        self.assertNotEqual(refresh_cookie, refresh_response.cookies['unipeer_refresh'].value)

    def test_logout_clears_cookies_and_revokes_refresh_tokens(self):
        self.client.post('/api/login/', {'email': 'auth@example.com', 'password': 'secret123'}, format='json')

        response = self.client.post('/api/logout/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['unipeer_access']['max-age'], 0)
        self.assertEqual(response.cookies['unipeer_refresh']['max-age'], 0)


class CookieAuthMiddlewareTests(SimpleTestCase):
    def test_middleware_reads_access_cookie_for_websocket_scope(self):
        async def run_test():
            class DummyInner:
                async def __call__(self, scope, receive, send):
                    return scope['user']

            middleware = CookieJWTAuthMiddleware(DummyInner())
            scope = {
                'type': 'websocket',
                'query_string': b'',
                'headers': [],
                'cookies': {'unipeer_access': 'not-a-real-token'},
            }
            result = await middleware(scope, None, None)
            self.assertEqual(result.__class__.__name__, 'AnonymousUser')

        asyncio.run(run_test())


class AdminAnalyticsAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin-user',
            password='secret123',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True,
        )
        self.admin_profile = StudentProfile.objects.create(user=self.admin_user, department='CS', year_of_study=4, email_verified=True)

        self.regular_user = User.objects.create_user(
            username='regular-user',
            password='secret123',
            email='regular@example.com',
        )
        self.regular_profile = StudentProfile.objects.create(user=self.regular_user, department='Math', year_of_study=2, email_verified=True)

    def test_profile_payload_includes_admin_flag(self):
        response = self.client.get(f'/api/profiles/{self.admin_profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_admin'])
        self.assertEqual(response.data['role'], 'admin')

        dashboard_response = self.client.get(f'/api/profiles/{self.admin_profile.id}/dashboard/')
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertTrue(dashboard_response.data['profile']['is_admin'])

    def test_non_admin_cannot_access_analytics_overview(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/analytics/overview/', {'profile_id': self.admin_profile.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_analytics_overview_and_export(self):
        self.client.force_authenticate(user=self.admin_user)

        overview_response = self.client.get('/api/analytics/overview/', {'profile_id': self.admin_profile.id})
        self.assertEqual(overview_response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', overview_response.data)
        self.assertIn('user_activity', overview_response.data['overview'])
        self.assertIn('most_used_skills', overview_response.data['overview'])
        self.assertIn('engagement_trend', overview_response.data['overview'])

        export_response = self.client.post('/api/analytics/export/', {'profile_id': self.admin_profile.id, 'format': 'csv'}, format='json')
        self.assertEqual(export_response.status_code, status.HTTP_200_OK)
        self.assertIn('csv', export_response.data)
        self.assertIn('download_url', export_response.data)


class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='analytics-user',
            password='secret123',
            email='analytics@example.com',
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            department='CS',
            year_of_study=3,
        )

        self.other_user = User.objects.create_user(
            username='analytics-other',
            password='secret123',
            email='otheranalytics@example.com',
        )
        self.other_profile = StudentProfile.objects.create(
            user=self.other_user,
            department='Math',
            year_of_study=2,
        )

        self.python = Skill.objects.create(name='Python')
        self.js = Skill.objects.create(name='JavaScript')
        self.profile.skills.add(self.python, self.js)
        self.other_profile.skills.add(self.python)

        self.room = CollaborationRoom.objects.create(name='Analytics Room', room_type='study')
        self.room.members.add(self.profile, self.other_profile)

        Message.objects.create(room=self.room, sender=self.profile, content='Hello there', timestamp=timezone.now())
        Message.objects.create(room=self.room, sender=self.profile, content='Second message', timestamp=timezone.now())
        Message.objects.create(room=self.room, sender=self.other_profile, content='Reply', timestamp=timezone.now())

        self.match = Match.objects.create(
            student_a=self.profile,
            student_b=self.other_profile,
            similarity_score=0.95,
            match_reason='Strong overlap',
            status='accepted'
        )

    def test_overview_endpoint_returns_expected_analytics_shape(self):
        response = self.client.get('/api/analytics/overview/', {'profile_id': self.profile.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertEqual(response.data['overview']['matches_made'], 1)
        self.assertEqual(response.data['overview']['messages_sent'], 2)
        self.assertIn('most_used_skills', response.data['overview'])
        self.assertIn('engagement_trend', response.data['overview'])

    def test_export_endpoint_returns_json_download_payload(self):
        response = self.client.post(
            '/api/analytics/export/',
            {'profile_id': self.profile.id, 'format': 'json'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        self.assertIn('overview', response.data)


class ResourceUploadAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resource-owner',
            password='secret123',
            email='owner@example.com',
        )
        self.profile = StudentProfile.objects.create(user=self.user, department='CS', year_of_study=2)

        self.other_user = User.objects.create_user(
            username='resource-other',
            password='secret123',
            email='other@example.com',
        )
        self.other_profile = StudentProfile.objects.create(user=self.other_user, department='Math', year_of_study=3)

    def test_authenticated_user_can_upload_file_resource(self):
        self.client.force_authenticate(user=self.user)

        upload = SimpleUploadedFile(
            'notes.txt',
            b'Graph theory notes',
            content_type='text/plain',
        )

        response = self.client.post(
            '/api/resources/',
            {
                'title': 'Graph Theory Notes',
                'description': 'Useful revision summary',
                'resource_type': 'article',
                'difficulty': 'beginner',
                'file': upload,
                'uploader_id': str(self.profile.id),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource = Resource.objects.get()
        self.assertEqual(resource.uploaded_by, self.user)
        self.assertTrue(resource.file.name.endswith('notes.txt'))

    def test_authenticated_user_cannot_spoof_uploader_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            '/api/resources/',
            {
                'title': 'Spoofed Upload',
                'description': 'Should be rejected',
                'resource_type': 'article',
                'difficulty': 'beginner',
                'url': 'https://example.com/resource',
                'uploader_id': str(self.other_profile.id),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Resource.objects.count(), 0)
