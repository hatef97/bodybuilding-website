from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import WeightLogViewSet, BodyMeasurementViewSet, ProgressLogViewSet


# Initialize the router
router = DefaultRouter()

# Register viewsets with the router
router.register(r'weight-logs', WeightLogViewSet, basename='weightlog')
router.register(r'body-measurements', BodyMeasurementViewSet, basename='bodymeasurement')
router.register(r'progress-logs', ProgressLogViewSet, basename='progresslog')

urlpatterns = [
    path('', include(router.urls)),
]
