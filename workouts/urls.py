from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ExerciseViewSet, WorkoutPlanViewSet, WorkoutLogViewSet



# Create a router
router = DefaultRouter()

# Register your viewsets with appropriate routes
router.register(r'workout-plans', WorkoutPlanViewSet, basename='workoutplan')
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workout-logs', WorkoutLogViewSet, basename='workout-log')

# Include the router-generated URLs in your app's URL configuration
urlpatterns = [
    path('', include(router.urls)),  # Include all router-generated URLs
]
