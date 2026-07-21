from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Accept access tokens from either the Authorization header or an HttpOnly cookie."""

    def authenticate(self, request):
        header = request.headers.get('Authorization', '')
        if header.startswith('Bearer '):
            return super().authenticate(request)

        access_token = request.COOKIES.get('unipeer_access')
        if not access_token:
            return None

        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return user, validated_token
        except Exception:
            return None
