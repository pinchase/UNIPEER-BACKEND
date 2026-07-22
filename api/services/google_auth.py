from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from api.models import StudentProfile

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Verify Google ID tokens and create or link local users without replacing the existing auth system."""

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or getattr(settings, 'GOOGLE_CLIENT_ID', '')
        self.client_secret = client_secret or getattr(settings, 'GOOGLE_CLIENT_SECRET', '')

    def verify_token(self, token: str) -> dict[str, Any]:
        if not token:
            raise ValueError('Google token is required.')
        if not self.client_id:
            raise ValueError('Google client ID is not configured.')

        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': token},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get('aud') != self.client_id:
            raise ValueError('Google token audience mismatch.')

        if payload.get('email_verified') not in {'true', True}:
            raise ValueError('Google email is not verified.')

        email = (payload.get('email') or '').strip().lower()
        if not email:
            raise ValueError('Google email is required.')

        return {
            'email': email,
            'given_name': payload.get('given_name') or payload.get('name') or email.split('@', 1)[0],
            'family_name': payload.get('family_name') or '',
            'picture': payload.get('picture') or '',
        }

    def authenticate(self, token: str) -> tuple[User, StudentProfile]:
        payload = self.verify_token(token)
        email = payload['email']

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).order_by('-id').first()
            if user is None:
                username = self._build_username(email)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    first_name=payload.get('given_name', ''),
                    last_name=payload.get('family_name', ''),
                )
            else:
                user.first_name = payload.get('given_name', user.first_name or '')
                user.last_name = payload.get('family_name', user.last_name or '')
                user.save(update_fields=['first_name', 'last_name'])

            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.email_verified = True
            if payload.get('picture') and not profile.avatar_url:
                profile.avatar_url = payload['picture']
            profile.save(update_fields=['email_verified', 'avatar_url'])

        return user, profile

    def _build_username(self, email: str) -> str:
        base = email.split('@', 1)[0].replace('.', '').replace('_', '')
        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{suffix}'
            suffix += 1
        return username
