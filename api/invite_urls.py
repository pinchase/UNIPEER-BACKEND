from django.urls import path
from rest_framework.routers import DefaultRouter
from .invite_views import InviteViewSet

router = DefaultRouter()
router.register(r'', InviteViewSet, basename='invite')

urlpatterns = router.urls
