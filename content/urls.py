from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, VideoViewSet



router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [
    path('', include(router.urls)),
]