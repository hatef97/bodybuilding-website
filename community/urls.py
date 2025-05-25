from rest_framework.routers import DefaultRouter

from .views import ForumPostViewSet, CommentViewSet, ChallengeViewSet, LeaderboardViewSet, UserProfileViewSet



router = DefaultRouter()
router.register(r'forum_posts', ForumPostViewSet, basename='forumpost')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboard')
router.register(r'user_profiles', UserProfileViewSet, basename='userprofile')

urlpatterns = router.urls
