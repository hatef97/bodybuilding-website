from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin
from django.conf import settings 
from django.urls import path, include, re_path



schema_view = get_schema_view(
   openapi.Info(
      title="Bodybuilding API",
      default_version='v1',
      description="API documentation for Bodybuilding Website",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="hatef.barin97@gmail.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),  # 👈 registration, activation, reset, etc.
    path('auth/', include('djoser.urls.authtoken')),  # 👈 login/logout using tokens
    path('workout/', include('workouts.urls')),  # Include workout-related API URLs
    path('nutrition/', include('nutrition.urls')),  # Include nutrion-related API URLs
    path('progress/', include('progress.urls')),    # Include progress-related API URLs
    path('community/', include('community.urls')),    # Include community-related API URLs
    path('content/', include('content.urls')),    # Include content-related API URLs
    path('store/', include('store.urls')),    # Include store-related API URLs
    # Swagger UI (HTML view)
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # ReDoc (Alternative documentation)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Raw JSON/YAML schema
    re_path(r'^swagger\.(?P<format>json|yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]



if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    