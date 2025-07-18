from datetime import timedelta, date
import pprint, math

from django.conf import settings
from django.test import override_settings
from django.urls import include, path, reverse, get_resolver
from django.utils import timezone

from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory

from core.models import CustomUser as User
from content.models import Video, Article, ExerciseGuide, FitnessMeasurement
from content.serializers import VideoSerializer, ArticleSerializer, FitnessMeasurementSerializer
from content.views import VideoViewSet, ArticleViewSet, FitnessMeasurementViewSet



class ArticleViewSetTests(APITestCase):
    def setUp(self):
        # Create a test user and get the user token for authenticated requests
        self.user = User.objects.create_user(username='testuser', password='password123', email="test@example.com")
        self.other_user = User.objects.create_user(username='otheruser', password='password123', email="other@example.com")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Create test articles
        self.article_1 = Article.objects.create(
            title='Published Article 1',
            excerpt='Excerpt 1',
            content='Content of article 1',
            status='published',
            is_published=True,
            author=self.user,
            published_at=timezone.now() - timedelta(days=1)
        )
        self.article_2 = Article.objects.create(
            title='Draft Article 2',
            excerpt='Excerpt 2',
            content='Content of article 2',
            status='draft',
            is_published=False,
            author=self.user
        )

    def test_create_article_authenticated(self):
        """Test creating an article with valid data (authenticated user)"""
        url = reverse('article-list')
        payload = {
            'author_id': self.user.id,
            'title': 'New Article',
            'excerpt': 'This is a new article',
            'content': 'Content of the new article',
            'status': 'draft',
            'is_published': False
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(id=response.data['id'])
        self.assertEqual(article.title, 'New Article')

    def test_create_article_unauthenticated(self):
        """Test creating an article when not authenticated"""
        self.client.credentials()  # Remove token from headers
        url = reverse('article-list')
        payload = {
            'author_id': self.user.id,
            'title': 'New Article',
            'excerpt': 'This is a new article',
            'content': 'Content of the new article',
            'status': 'draft',
            'is_published': False
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_article_without_author(self):
        """Test creating an article without providing author_id should raise validation error"""
        url = reverse('article-list')
        payload = {
            'title': 'New Article Without Author',
            'excerpt': 'This article has no author',
            'content': 'Content of this article',
            'status': 'draft',
            'is_published': False
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('author', response.data)

    def test_update_article(self):
        """Test updating an article"""
        url = reverse('article-detail', kwargs={'slug': self.article_2.slug})
        payload = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'status': 'published',
            'is_published': True
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article = Article.objects.get(id=self.article_2.id)
        self.assertEqual(article.title, 'Updated Title')
        self.assertTrue(article.is_published)
        self.assertIsNotNone(article.published_at)  # Ensure the published_at is set

    def test_filter_by_author(self):
        """Test filtering articles by author"""
        url = reverse('article-list') + '?author__username=testuser'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should return both articles created by 'testuser'

    def test_filter_by_status(self):
        """Test filtering articles by status"""
        url = reverse('article-list') + '?status=published'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one published article

    def test_ordering_by_published_at(self):
        """Test ordering articles by published_at"""
        url = reverse('article-list') + '?ordering=-published_at'  # Correct ordering direction
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure that the articles are ordered correctly
        self.assertEqual(response.data[0]['id'], self.article_1.id)  # article_1 should be the first
        self.assertEqual(response.data[1]['id'], self.article_2.id)  # article_2 should be the second
        
    def test_search_article(self):
        """Test search functionality on title, excerpt, and content"""
        url = reverse('article-list') + '?search=Excerpt 1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return article 1

    def test_recent_endpoint(self):
        """Test the custom '/recent/' endpoint"""
        url = reverse('article-recent')  # Assuming the recent action is registered with the name 'article-recent'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only published articles should be returned

    def test_permissions_article_edit(self):
        """Test that only the author or staff can edit an article"""
        # As non-author
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.other_user).key)
        url = reverse('article-detail', kwargs={'slug': self.article_2.slug})
        payload = {'title': 'Invalid Update', 'content': 'This should not be allowed'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # As author
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_only_fields(self):
        """Test that read-only fields (slug, created_at, updated_at) cannot be updated"""
        url = reverse('article-detail', kwargs={'slug': self.article_2.slug})
        payload = {'slug': 'new-slug'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article = Article.objects.get(id=self.article_2.id)
        self.assertNotEqual(article.slug, 'new-slug')  # Ensure slug has not been updated



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



class FitnessMeasurementViewSetTests(APITestCase):

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

        # Base dates
        today = timezone.now().date()
        past = today - timedelta(days=365 * 30)  # 30 years ago
        older = today - timedelta(days=365 * 40)  # 40 years ago

        # Create some measurements
        self.fm1 = FitnessMeasurement.objects.create(
            user=self.user1,
            height_cm=170,
            weight_kg=70.0,
            gender=FitnessMeasurement.GENDER_MALE,
            date_of_birth=past,
        )
        self.fm2 = FitnessMeasurement.objects.create(
            user=self.user2,
            height_cm=160,
            weight_kg=60.0,
            gender=FitnessMeasurement.GENDER_FEMALE,
            date_of_birth=older,
        )
        # A third with no gender or dob
        self.fm3 = FitnessMeasurement.objects.create(
            user=self.user1,
            height_cm=180,
            weight_kg=80.0,
        )


    def test_list_all_measurements(self):
        url = reverse("fitnessmeasurement-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Expect 3 total
        self.assertEqual(len(resp.data), 3)


    def test_retrieve_includes_computed_fields(self):
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data

        # Check raw fields
        self.assertEqual(data["height_cm"], 170)
        self.assertEqual(data["weight_kg"], 70.0)

        # Computed values
        expected_height_m = 1.70
        expected_bmi = round(70.0 / (expected_height_m * expected_height_m), 2)
        self.assertAlmostEqual(data["height_m"], expected_height_m, places=2)
        self.assertAlmostEqual(data["bmi"], expected_bmi, places=2)
        # BMI category
        self.assertEqual(data["bmi_category"], self.fm1.bmi_category)
        # BSA
        expected_bsa = round(math.sqrt((170 * 70.0) / 3600.0), 2)
        self.assertAlmostEqual(data["bsa"], expected_bsa, places=2)

        # URL field
        detail_url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        self.assertTrue(data["url"].endswith(detail_url))


    def test_filter_by_username(self):
        url = reverse("fitnessmeasurement-list") + f"?user__username={self.user1.username}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Only fm1 and fm3 belong to alice
        self.assertEqual({m["id"] for m in resp.data}, {self.fm1.id, self.fm3.id})


    def test_filter_by_gender(self):
        url = reverse("fitnessmeasurement-list") + f"?gender={FitnessMeasurement.GENDER_FEMALE}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], self.fm2.id)


    def test_filter_by_date_of_birth(self):
        dob_str = self.fm2.date_of_birth.isoformat()
        url = reverse("fitnessmeasurement-list") + f"?date_of_birth={dob_str}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], self.fm2.id)


    def test_search_on_username(self):
        url = reverse("fitnessmeasurement-list") + "?search=ali"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # 'ali' matches 'alice'
        self.assertTrue(all(m["user"] == str(self.user1) for m in resp.data))


    def test_ordering_by_height_and_weight(self):
        # ascending height_cm
        url = reverse("fitnessmeasurement-list") + "?ordering=height_cm"
        resp = self.client.get(url)
        heights = [m["height_cm"] for m in resp.data]
        self.assertEqual(heights, sorted(heights))

        # descending weight_kg
        url = reverse("fitnessmeasurement-list") + "?ordering=-weight_kg"
        resp = self.client.get(url)
        weights = [m["weight_kg"] for m in resp.data]
        self.assertEqual(weights, sorted(weights, reverse=True))


    def test_unauthenticated_create_forbidden(self):
        payload = {"height_cm": 160, "weight_kg": 60.0, "gender": "", "date_of_birth": None}
        resp = self.client.post(reverse("fitnessmeasurement-list"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_authenticated_create_defaults_user(self):
        self.client.force_authenticate(self.user1)
        payload = {"height_cm": 165, "weight_kg": 65.0}
        resp = self.client.post(reverse("fitnessmeasurement-list"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = FitnessMeasurement.objects.get(pk=resp.data["id"])
        self.assertEqual(created.user, self.user1)


    def test_admin_create_for_other_user_with_user_id(self):
        self.client.force_authenticate(self.staff)
        payload = {"user_id": self.user2.id, "height_cm": 150, "weight_kg": 50.0}
        resp = self.client.post(reverse("fitnessmeasurement-list"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = FitnessMeasurement.objects.get(pk=resp.data["id"])
        self.assertEqual(created.user, self.user2)


    def test_owner_can_update(self):
        self.client.force_authenticate(self.user1)
        new_weight = 75.0
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        resp = self.client.patch(url, {"weight_kg": new_weight}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.fm1.refresh_from_db()
        self.assertEqual(self.fm1.weight_kg, new_weight)


    def test_non_owner_cannot_update(self):
        self.client.force_authenticate(self.user2)
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        resp = self.client.patch(url, {"weight_kg": 80.0}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


    def test_staff_can_update_any(self):
        self.client.force_authenticate(self.staff)
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        resp = self.client.patch(url, {"weight_kg": 80.0}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)



    def test_owner_can_delete(self):
        self.client.force_authenticate(self.user1)
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm3.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FitnessMeasurement.objects.filter(pk=self.fm3.pk).exists())



    def test_non_owner_cannot_delete(self):
        self.client.force_authenticate(self.user2)
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm1.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


    def test_staff_can_delete_any(self):
        self.client.force_authenticate(self.staff)
        url = reverse("fitnessmeasurement-detail", kwargs={"pk": self.fm2.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        