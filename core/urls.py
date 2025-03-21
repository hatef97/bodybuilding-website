from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import *



# Create the main router for users
router = DefaultRouter()
router.register(r'signup', UserRegistrationViewSet, basename='signup')
router.register(r'profile', UserProfileViewSet, basename='user-profile')
router.register(r'account', ChangePasswordViewSet, basename='account')


# Include the main router and the nested router
urlpatterns = router.urls
