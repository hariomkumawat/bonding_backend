"""
Main URL Configuration for Bonding App
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from bondingapp.core.views import index
urlpatterns = [
    path('', index, name='home'),
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    
    # path('__debug__/', include('debug_toolbar.urls')),
    
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('api/token/verify/', TokenVerifyView.as_view()),
    # API Endpoints
    path('api/', include('bondingapp.core.urls')),
    # path('api/auth/', include('apps.authentication.urls')),
    # path('api/users/', include('apps.users.urls')),
    # path('api/activities/', include('apps.activities.urls')),
    # path('api/progress/', include('apps.gamification.urls')),  # Progress & stats
    # path('api/rewards/', include('apps.gamification.urls')),   # Rewards endpoints
    # path('api/partner/', include('apps.users.urls')),          # Partner endpoints
    # path('api/settings/', include('apps.users.urls')),         # Settings endpoints
    # path('api/notifications/', include('apps.notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

# Customize admin site
admin.site.site_header = "Bonding App Administration"
admin.site.site_title = "Bonding App Admin"
admin.site.index_title = "Welcome to Bonding App Admin Panel"