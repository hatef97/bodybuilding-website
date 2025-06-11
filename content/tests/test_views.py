from datetime import timedelta
import pprint

from django.conf import settings
from django.test import override_settings
from django.urls import include, path, reverse, get_resolver
from django.utils import timezone

from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.test import APITestCase, APIRequestFactory

from core.models import CustomUser as User
from content.models import Video, Article, ExerciseGuide
from content.serializers import VideoSerializer, ArticleSerializer
from content.views import VideoViewSet, ArticleViewSet



class ArticleViewSetTests(APITestCase):

    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass"
        )
        self.staff = User.objects.create_user(
            username="admin", email="admin@example.com", password="pass", is_staff=True
        )

        # A draft for alice
        self.draft = Article.objects.create(
            author=self.user1,
            title="Draft Article",
            excerpt="Draft excerpt",
            content="Draft content",
            status=Article.STATUS_DRAFT,
            is_published=False,
        )

        # Two published for alice
        self.old = Article.objects.create(
            author=self.user1,
            title="Old Pub",
            excerpt="Old excerpt",
            content="Old content",
            status=Article.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=5),
        )
        self.new = Article.objects.create(
            author=self.user1,
            title="New Pub",
            excerpt="New excerpt",
            content="New content",
            status=Article.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )

        # Six more for recent() – only top 5 should return
        for i in range(6):
            Article.objects.create(
                author=self.user1,
                title=f"Recent {i}",
                excerpt=f"Recent excerpt {i}",
                content=f"Recent content {i}",
                status=Article.STATUS_PUBLISHED,
                is_published=True,
                published_at=timezone.now() - timedelta(hours=i),
            )

        # One published for bob
        self.bob_article = Article.objects.create(
            author=self.user2,
            title="Bob's Article",
            excerpt="Bob excerpt",
            content="Bob content",
            status=Article.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=2),
        )


    def test_list_articles(self):
        url = reverse("article-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), Article.objects.count())


    def test_retrieve_article(self):
        url = reverse("article-detail", kwargs={"slug": self.new.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["slug"], self.new.slug)
        self.assertEqual(resp.data["title"], self.new.title)


    def test_filter_by_is_published(self):
        url = reverse("article-list") + "?is_published=True"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected = Article.objects.filter(is_published=True).count()
        self.assertEqual(len(resp.data), expected)


    def test_filter_by_author_username(self):
        url = reverse("article-list") + f"?author__username={self.user1.username}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for art in resp.data:
            self.assertEqual(art["author"], str(self.user1))


    def test_filter_by_status(self):
        url = reverse("article-list") + f"?status={Article.STATUS_DRAFT}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for art in resp.data:
            self.assertEqual(art["status"], Article.STATUS_DRAFT)


    def test_search_title_excerpt_content(self):
        url = reverse("article-list") + "?search=New"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = {a["slug"] for a in resp.data}
        self.assertIn(self.new.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)


    def test_ordering_by_published_at_ascending(self):
        url = reverse("article-list") + "?ordering=published_at"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dates = [
            timezone.datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
            for a in resp.data
            if a["published_at"]
        ]
        self.assertEqual(dates, sorted(dates))


    def test_ordering_by_title(self):
        url = reverse("article-list") + "?ordering=title"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in resp.data]
        self.assertEqual(titles, sorted(titles))


    def test_unauthenticated_create_forbidden(self):
        url = reverse("article-list")
        payload = {
            "title": "Anon",
            "excerpt": "Anon",
            "content": "Anon",
            "status": Article.STATUS_DRAFT,
            "is_published": False,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_default_author_and_draft(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("article-list")
        payload = {
            "title": "Alice Draft",
            "excerpt": "Draft",
            "content": "Draft",
            "status": Article.STATUS_DRAFT,
            "is_published": False,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author"], str(self.user1))
        self.assertIsNone(resp.data["published_at"])


    def test_create_and_publish_sets_published_at(self):
        self.client.force_authenticate(user=self.user1)
        before = timezone.now()
        url = reverse("article-list")
        payload = {
            "title": "Alice Publish",
            "excerpt": "Publish",
            "content": "Publish",
            "status": Article.STATUS_PUBLISHED,
            "is_published": True,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        pub_dt = timezone.datetime.fromisoformat(
            resp.data["published_at"].replace("Z", "+00:00")
        )
        self.assertGreaterEqual(pub_dt, before)


    def test_update_toggle_publish_sets_published_at(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("article-detail", kwargs={"slug": self.draft.slug})
        resp = self.client.patch(url, {"is_published": True}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pub_dt = timezone.datetime.fromisoformat(
            resp.data["published_at"].replace("Z", "+00:00")
        )
        self.assertIsNotNone(pub_dt)


    def test_forbid_update_by_non_author(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse("article-detail", kwargs={"slug": self.draft.slug})
        resp = self.client.patch(url, {"is_published": True}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


    def test_staff_can_update_any(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse("article-detail", kwargs={"slug": self.draft.slug})
        resp = self.client.patch(url, {"is_published": True}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_recent_action(self):
        url = reverse("article-recent")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        self.assertEqual(len(data), 5)
        dates = [
            timezone.datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            for item in data
        ]
        # descending published_at
        self.assertTrue(all(dates[i] >= dates[i+1] for i in range(len(dates)-1)))
        # all published
        for art in data:
            self.assertTrue(art["is_published"])



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



class ExerciseGuideViewSetTests(APITestCase):

    def setUp(self):
        # Users: regular and staff
        self.alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )
        self.bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass"
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="pass", is_staff=True
        )

        # Two guides by Alice
        self.guide1 = ExerciseGuide.objects.create(
            author=self.alice,
            name="Push Up",
            excerpt="Push up description",
            steps="1. Plank\n2. Lower\n3. Raise",
            difficulty=ExerciseGuide.DIFFICULTY_BEGINNER,
            primary_muscle="Chest",
            equipment_required="None",
            video_embed="<iframe></iframe>",
        )
        self.guide2 = ExerciseGuide.objects.create(
            author=self.alice,
            name="Squat",
            excerpt="Squat description",
            steps="1. Stand\n2. Bend knees\n3. Rise",
            difficulty=ExerciseGuide.DIFFICULTY_ADVANCED,
            primary_muscle="Legs",
            equipment_required="Barbell",
            video_embed="",
        )

        # One guide by Bob
        self.bob_guide = ExerciseGuide.objects.create(
            author=self.bob,
            name="Lunge",
            excerpt="Lunge description",
            steps="1. Step\n2. Bend\n3. Return",
            difficulty=ExerciseGuide.DIFFICULTY_INTERMEDIATE,
            primary_muscle="Legs",
            equipment_required="None",
            video_embed="",
        )

        # Additional guides for ordering/search
        for i in range(3):
            ExerciseGuide.objects.create(
                author=self.alice,
                name=f"Guide {i}",
                excerpt="X",
                steps="Step",
                difficulty=ExerciseGuide.DIFFICULTY_BEGINNER,
            )


    def test_list_all_guides(self):
        url = reverse("exerciseguide-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Total: 2 (Alice) +1 (Bob) +3 extra =6
        self.assertEqual(len(resp.data), ExerciseGuide.objects.count())


    def test_retrieve_guide(self):
        url = reverse("exerciseguide-detail", kwargs={"slug": self.guide1.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["slug"], self.guide1.slug)
        self.assertEqual(resp.data["name"], "Push Up")


    def test_filter_by_difficulty(self):
        url = reverse("exerciseguide-list") + f"?difficulty={ExerciseGuide.DIFFICULTY_ADVANCED}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertEqual(item["difficulty"], ExerciseGuide.DIFFICULTY_ADVANCED)


    def test_filter_by_author_username(self):
        url = reverse("exerciseguide-list") + f"?author__username={self.bob.username}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["author"], str(self.bob))


    def test_search_name_excerpt_steps(self):
        # search "Squat" should return guide2
        url = reverse("exerciseguide-list") + "?search=Squat"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = [g["slug"] for g in resp.data]
        self.assertIn(self.guide2.slug, slugs)
        self.assertNotIn(self.guide1.slug, slugs)


    def test_ordering_by_name(self):
        url = reverse("exerciseguide-list") + "?ordering=name"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.data]
        self.assertEqual(names, sorted(names))


    def test_unauthenticated_cannot_create(self):
        url = reverse("exerciseguide-list")
        payload = {
            "author_id": self.alice.id,
            "name": "New Guide",
            "excerpt": "Desc",
            "steps": "Do it",
            "difficulty": ExerciseGuide.DIFFICULTY_BEGINNER,
            "primary_muscle": "",
            "equipment_required": "",
            "video_embed": "",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_authenticated_create_default_author(self):
        self.client.force_authenticate(user=self.alice)
        url = reverse("exerciseguide-list")
        payload = {
            # omit author_id: perform_create will set to request.user
            "name": "New Guide",
            "excerpt": "Desc",
            "steps": "Do it",
            "difficulty": ExerciseGuide.DIFFICULTY_BEGINNER,
            "primary_muscle": "Arms",
            "equipment_required": "None",
            "video_embed": "",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author"], str(self.alice))
        self.assertTrue(resp.data["slug"].startswith("new-guide"))


    def test_forbid_update_by_non_author(self):
        self.client.force_authenticate(user=self.bob)
        url = reverse("exerciseguide-detail", kwargs={"slug": self.guide1.slug})
        resp = self.client.patch(url, {"name": "Changed"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


    def test_author_can_update(self):
        self.client.force_authenticate(user=self.alice)
        url = reverse("exerciseguide-detail", kwargs={"slug": self.guide2.slug})
        resp = self.client.patch(url, {"excerpt": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["excerpt"], "Updated")


    def test_staff_can_update_any(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("exerciseguide-detail", kwargs={"slug": self.bob_guide.slug})
        resp = self.client.patch(url, {"excerpt": "Admin Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["excerpt"], "Admin Updated")


    def test_delete_by_author(self):
        self.client.force_authenticate(user=self.alice)
        url = reverse("exerciseguide-detail", kwargs={"slug": self.guide1.slug})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ExerciseGuide.objects.filter(pk=self.guide1.pk).exists())


    def test_delete_forbidden_to_non_author(self):
        self.client.force_authenticate(user=self.bob)
        url = reverse("exerciseguide-detail", kwargs={"slug": self.guide1.slug})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
