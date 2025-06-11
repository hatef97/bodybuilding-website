from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, VideoViewSet, ExerciseGuideViewSet, FitnessMeasurementViewSet



router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"exercise-guides", ExerciseGuideViewSet, basename="exerciseguide")
router.register(r"measurements", FitnessMeasurementViewSet, basename="fitnessmeasurement")



urlpatterns = [
    path('', include(router.urls)),
]
