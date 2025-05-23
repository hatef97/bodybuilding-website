from rest_framework.routers import DefaultRouter

from .views import ForumPostViewSet, CommentViewSet, ChallengeViewSet, LeaderboardViewSet



router = DefaultRouter()
router.register(r'forum_posts', ForumPostViewSet, basename='forumpost')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboard')

urlpatterns = router.urls
