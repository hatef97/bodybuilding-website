from rest_framework.routers import DefaultRouter

from .views import ForumPostViewSet



router = DefaultRouter()
router.register(r'forum_posts', ForumPostViewSet, basename='forumpost')

urlpatterns = router.urls