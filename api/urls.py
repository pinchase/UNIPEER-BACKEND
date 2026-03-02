"""
API URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'skills', views.SkillViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'profiles', views.StudentProfileViewSet)
router.register(r'resources', views.ResourceViewSet)
router.register(r'rooms', views.CollaborationRoomViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'matches', views.MatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('stats/', views.platform_stats, name='platform-stats'),
]
