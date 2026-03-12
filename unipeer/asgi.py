"""ASGI entrypoint for HTTP + WebSocket traffic."""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unipeer.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from api.routing import websocket_urlpatterns
from api.ws_auth import QueryStringJWTAuthMiddlewareStack

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
	'http': django_asgi_app,
	'websocket': AllowedHostsOriginValidator(
		QueryStringJWTAuthMiddlewareStack(
			URLRouter(websocket_urlpatterns)
		)
	),
})
