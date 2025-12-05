"""
URL Configuration for Bonding App API
Location: bondingapp/core/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bondingapp.core.views import (
    AuthViewSet,
    UserViewSet,
    ActivityViewSet,
    ProgressViewSet,
    RewardViewSet,
    PartnerViewSet,
    NotificationViewSet,
    SettingsViewSet,
)

# Create the main router
router = DefaultRouter()

# Register ViewSets (excluding auth for custom handling)
router.register(r'users', UserViewSet, basename='users')
router.register(r'activities', ActivityViewSet, basename='activities')
router.register(r'progress', ProgressViewSet, basename='progress')
router.register(r'rewards', RewardViewSet, basename='rewards')
router.register(r'partner', PartnerViewSet, basename='partner')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'settings', SettingsViewSet, basename='settings')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints (explicit for clarity)
    path('auth/google-login/', AuthViewSet.as_view({'post': 'google_login'}), name='google-login'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('auth/register/', AuthViewSet.as_view({'post': 'register'}), name='register'),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
    
    # All other ViewSet routes
    path('', include(router.urls)),
]