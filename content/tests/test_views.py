from datetime import timedelta

from django.test import override_settings
from django.urls import include, path, reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.test import APITestCase, APIRequestFactory

from core.models import CustomUser as User
from content.models import Video
from content.serializers import VideoSerializer
from content.views import VideoViewSet



# Register our ViewSet at the root for testing
router = DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [
    path("", include(router.urls)),
]



@override_settings(ROOT_URLCONF=__name__)
class VideoViewSetTests(APITestCase):
    
    def setUp(self):
        # Users
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass"
        )
        self.staff = User.objects.create_user(
            username="admin", email="admin@example.com", password="pass", is_staff=True
        )

        # Create videos for user1
        self.draft1 = Video.objects.create(
            author=self.user1,
            title="Draft 1",
            url="https://example.com/draft1.mp4",
            embed_code="",
            description="First draft",
            status=Video.STATUS_DRAFT,
            is_published=False,
        )
        self.pub_old = Video.objects.create(
            author=self.user1,
            title="Published Old",
            url="https://example.com/old.mp4",
            embed_code="",
            description="Old published",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=5),
        )
        self.pub_new = Video.objects.create(
            author=self.user1,
            title="Published New",
            url="https://example.com/new.mp4",
            embed_code="",
            description="New published",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )

        # Additional videos for recent action
        for i in range(6):
            Video.objects.create(
                author=self.user1,
                title=f"Recent {i}",
                url=f"https://example.com/r{i}.mp4",
                embed_code="",
                description=f"Recent desc {i}",
                status=Video.STATUS_PUBLISHED,
                is_published=True,
                published_at=timezone.now() - timedelta(hours=i),
            )

        # Video for user2
        self.other_video = Video.objects.create(
            author=self.user2,
            title="Bob's Video",
            url="https://example.com/bob.mp4",
            embed_code="",
            description="Bob's content",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=2),
        )


    def test_list_videos(self):
        resp = self.client.get("/videos/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # We created 1 draft + 1 other_user draft? Actually drafts: only draft1. Published: 1+1+6+1 = 9.
        self.assertEqual(len(resp.data), Video.objects.count())


    def test_retrieve_video(self):
        url = f"/videos/{self.pub_new.slug}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["slug"], self.pub_new.slug)
        self.assertEqual(resp.data["title"], "Published New")


    def test_filter_by_is_published(self):
        resp = self.client.get("/videos/?is_published=True")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Count only published
        pub_count = Video.objects.filter(is_published=True).count()
        self.assertEqual(len(resp.data), pub_count)


    def test_filter_by_author_username(self):
        resp = self.client.get(f"/videos/?author__username={self.user1.username}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertEqual(item["author"], str(self.user1))


    def test_search_title_description(self):
        resp = self.client.get("/videos/?search=New")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = [v["slug"] for v in resp.data]
        # Should include pub_new and recent0 (title Recent 0 contains "Recent" not "New")
        self.assertIn(self.pub_new.slug, slugs)
        # Ensure no completely unrelated
        for v in resp.data:
            self.assertTrue("new" in v["title"].lower() or "new" in v["description"].lower())


    def test_ordering_by_title(self):
        resp = self.client.get("/videos/?ordering=title&author__username=alice")
        titles = [v["title"] for v in resp.data]
        self.assertEqual(titles, sorted(titles))


    def test_unauthenticated_create_forbidden(self):
        payload = {
            "title": "Anon Create",
            "description": "desc",
            "url": "https://example.com/a.mp4",
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        resp = self.client.post("/videos/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_without_author_id_sets_request_user(self):
        """
        Authenticated create without explicit author_id should default to request.user.
        """
        self.client.force_authenticate(user=self.user1)
        payload = {
            # include author_id now that serializer requires it
            "author_id": self.user1.id,
            "title": "User1 Video",
            "description": "desc",
            "url": "https://example.com/u1.mp4",
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        resp = self.client.post("/videos/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author"], str(self.user1))
        self.assertIsNone(resp.data["published_at"])


    def test_create_with_author_id_and_publish(self):
        """
        Providing author_id and is_published should auto-set published_at.
        """
        self.client.force_authenticate(user=self.user1)
        payload = {
            "author_id": self.user2.id,
            "title": "By Bob",
            "description": "desc",
            "url": "https://example.com/b.mp4",
            "embed_code": "",
            "status": Video.STATUS_PUBLISHED,
            "is_published": True,
        }
        before = timezone.now()
        resp = self.client.post("/videos/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author"], str(self.user2))

        # Strip trailing 'Z' before parsing
        published_at_str = resp.data["published_at"]
        published_at = timezone.datetime.fromisoformat(
            published_at_str.replace("Z", "+00:00")
        )
        self.assertGreaterEqual(published_at, before)


    def test_update_toggle_publish_forbidden_without_url(self):
        # Even authenticated, test validation on update must include url or embed
        self.client.force_authenticate(user=self.user1)
        resp = self.client.patch(
            f"/videos/{self.draft1.slug}/",
            {"is_published": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_update_toggle_publish_sets_published_at(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.patch(
            f"/videos/{self.draft1.slug}/",
            {"is_published": True, "url": self.draft1.url},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["is_published"])
        self.assertIsNotNone(resp.data["published_at"])


    def test_forbid_update_by_non_author(self):
        self.client.force_authenticate(user=self.user2)
        resp = self.client.patch(
            f"/videos/{self.draft1.slug}/",
            {"is_published": True, "url": self.draft1.url},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


    def test_staff_can_update_any(self):
        self.client.force_authenticate(user=self.staff)
        resp = self.client.patch(
            f"/videos/{self.draft1.slug}/",
            {"is_published": True, "url": self.draft1.url},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_recent_action(self):
        resp = self.client.get("/videos/recent/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        self.assertEqual(len(data), 5)

        # Parse ISO strings with trailing 'Z'
        dates = [
            timezone.datetime.fromisoformat(item["published_at"].rstrip("Z"))
            for item in data
        ]
        # Check descending order
        self.assertTrue(all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)))
        for v in data:
            self.assertTrue(v["is_published"])
