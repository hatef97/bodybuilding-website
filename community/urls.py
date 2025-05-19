from rest_framework.routers import DefaultRouter

from .views import ForumPostViewSet, CommentViewSet



router = DefaultRouter()
router.register(r'forum_posts', ForumPostViewSet, basename='forumpost')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = router.urls
