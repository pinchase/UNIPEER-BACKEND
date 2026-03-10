from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class NotificationUserThrottle(UserRateThrottle):
	scope = 'notifications_user'


class NotificationAnonThrottle(AnonRateThrottle):
	scope = 'notifications_anon'


class NotificationBurstThrottle(SimpleRateThrottle):
	scope = 'notifications_burst'

	def get_cache_key(self, request, view):
		recipient_id = request.query_params.get('recipient_id', 'all')
		ident = self.get_ident(request)
		return self.cache_format % {
			'scope': self.scope,
			'ident': f'{ident}:{recipient_id}',
		}
