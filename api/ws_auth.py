from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import AccessToken, TokenError

UserModel = get_user_model()


@database_sync_to_async
def get_user_from_token(token):
    try:
        validated_token = AccessToken(token)
        user_id = validated_token.get('user_id')
        if not user_id:
            return AnonymousUser()
        return UserModel.objects.get(id=user_id)
    except (TokenError, UserModel.DoesNotExist, KeyError):
        return AnonymousUser()


class QueryStringJWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        scope['user'] = AnonymousUser()

        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = (params.get('token') or [None])[0]

        if token:
            scope['user'] = await get_user_from_token(token)

        return await super().__call__(scope, receive, send)


def QueryStringJWTAuthMiddlewareStack(inner):
    return QueryStringJWTAuthMiddleware(inner)
