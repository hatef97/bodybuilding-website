"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings 
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),  # 👈 registration, activation, reset, etc.
    path('auth/', include('djoser.urls.authtoken')),  # 👈 login/logout using tokens
    path('workout/', include('workouts.urls')),  # Include workout-related API URLs
    path('nutrition/', include('nutrition.urls')),  # Include nutrion-related API URLs
    path('progress/', include('progress.urls')),    # Include progress-related API URLs
    path('community/', include('community.urls')),    # Include community-related API URLs
    path('content/', include('content.urls')),    # Include content-related API URLs
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    