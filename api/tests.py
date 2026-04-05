from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CollaborationRoom, Match, MatchInvite, Notification, StudentProfile


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
