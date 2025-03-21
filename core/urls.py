from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import *



# Create the main router for users
router = DefaultRouter()
router.register(r'users', UserRegistrationViewSet, basename='user-registration')
router.register(r'profile', UserProfileViewSet, basename='user-profile')


# Create a nested router for user profile and password change under the 'users' endpoint
user_router = NestedDefaultRouter(router, r'users', lookup='user')
user_router.register(r'change-password', ChangePasswordViewSet, basename='change-password')  # Updated to ViewSet


# Include the main router and the nested router
urlpatterns = router.urls + user_router.urls
