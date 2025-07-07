import io, math
import tempfile
from datetime import timedelta, date

from django.test import TestCase, override_settings
from django.urls import include, path, reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.routers import DefaultRouter
from rest_framework.test import APIRequestFactory
from rest_framework.reverse import reverse as drf_reverse

from core.models import CustomUser as User
from content.models import Article, Video, ExerciseGuide
from content.serializers import ArticleSerializer, VideoSerializer, ExerciseGuideSerializer, FitnessMeasurementSerializer
from content.views import ArticleViewSet, VideoViewSet, FitnessMeasurement



class ArticleSerializerTests(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        # Another user for testing author_id behavior
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pwd"
        )

        # Request factory for serializer context
        self.factory = APIRequestFactory()

        # Draft article (no slug, no published_at)
        self.draft_article = Article.objects.create(
            author=self.user,
            title="Draft Title",
            excerpt="Draft excerpt",
            content="Draft content",
            status=Article.STATUS_DRAFT,
            is_published=False,
        )
        # Published article (slug auto-generated, published_at set by save())
        self.published_article = Article.objects.create(
            author=self.user,
            title="Published Title",
            excerpt="Published excerpt",
            content="Published content",
            status=Article.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )


    def test_serialize_article_fields(self):
        """
        Serializing an existing published article should include:
        - 'url' pointing to /articles/{slug}/
        - 'id', 'slug', 'author' (as str(user)), core fields, featured_image_url=None,
          status, is_published, published_at, created_at, updated_at
        - 'author_id' must NOT appear in the serialized output
        """
        request = self.factory.get("/articles/")
        serializer = ArticleSerializer(
            instance=self.published_article, context={"request": request}
        )
        data = serializer.data

        # URL should be absolute and correct
        expected_detail = reverse("article-detail", kwargs={"slug": self.published_article.slug})
        self.assertEqual(data["url"], f"http://testserver{expected_detail}")

        # ID and slug
        self.assertEqual(data["id"], self.published_article.id)
        self.assertEqual(data["slug"], self.published_article.slug)

        # Author should display str(self.user)
        self.assertEqual(data["author"], str(self.user))

        # Core content fields
        self.assertEqual(data["title"], "Published Title")
        self.assertEqual(data["excerpt"], "Published excerpt")
        self.assertEqual(data["content"], "Published content")

        # No featured_image initially, so featured_image_url is None
        self.assertIsNone(data["featured_image_url"])

        # Status / publication fields
        self.assertEqual(data["status"], Article.STATUS_PUBLISHED)
        self.assertTrue(data["is_published"])
        self.assertIsNotNone(data["published_at"])

        # Timestamps must be present
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        # author_id should not appear in read output
        self.assertNotIn("author_id", data)


    def test_deserialize_create_auto_slug_and_published_at(self):
        """
        Creating via serializer with is_published=True but no published_at
        should auto-set slug and published_at.
        """
        request = self.factory.post("/articles/")
        payload = {
            "author_id": self.user.id,
            "title": "New Article Title",
            "excerpt": "New excerpt",
            "content": "New content body",
            "status": Article.STATUS_PUBLISHED,
            "is_published": True,
            # published_at omitted
        }
        serializer = ArticleSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        article = serializer.save()

        # Slug generated from title
        self.assertTrue(article.slug.startswith("new-article-title"))

        # published_at auto-set to now (within a few seconds)
        self.assertIsNotNone(article.published_at)
        self.assertAlmostEqual(article.published_at, timezone.now(), delta=timedelta(seconds=5))

        # Author correctly set
        self.assertEqual(article.author, self.user)


    def test_update_toggle_publish_sets_published_at(self):
        """
        Updating a draft to is_published=True without published_at
        should auto-populate published_at.
        """
        request = self.factory.patch(f"/articles/{self.draft_article.slug}/")
        payload = {"is_published": True}
        serializer = ArticleSerializer(
            instance=self.draft_article, data=payload, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertTrue(updated.is_published)
        self.assertIsNotNone(updated.published_at)
        self.assertGreaterEqual(updated.published_at, self.draft_article.created_at)


    def test_slug_and_read_only_fields_ignored_on_update(self):
        """
        Passing 'slug', 'created_at', or 'updated_at' in data should be ignored.
        Other fields (like 'title') should update normally.
        """
        original_slug = self.draft_article.slug
        original_created = self.draft_article.created_at
        original_updated = self.draft_article.updated_at

        # Prepare a future timestamp
        future_dt = (timezone.now() + timedelta(days=10)).isoformat()

        payload = {
            "slug": "fake-slug",
            "created_at": future_dt,
            "updated_at": future_dt,
            "title": "Updated Title Only"
        }
        request = self.factory.put(f"/articles/{original_slug}/")
        serializer = ArticleSerializer(
            instance=self.draft_article, data=payload, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        # Slug remains unchanged
        self.assertEqual(updated.slug, original_slug)
        # created_at stays the same
        self.assertEqual(updated.created_at, original_created)
        # updated_at should be newer than original, but not equal to the fake future
        self.assertNotEqual(updated.updated_at, timezone.datetime.fromisoformat(future_dt))
        self.assertGreaterEqual(updated.updated_at, original_updated)

        # Title does update
        self.assertEqual(updated.title, "Updated Title Only")


    def test_featured_image_url_included_if_image_present(self):
        """
        If a featured_image is set on the article, the serializer returns
        a valid absolute URL under 'featured_image_url'.
        """
        # Create a small in-memory GIF
        image_content = (
            b"\x47\x49\x46\x38\x37\x61\x01\x00\x01\x00\x80\x00\x00\x00"
            b"\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        )
        temp_img = SimpleUploadedFile(
            name="test.gif",
            content=image_content,
            content_type="image/gif"
        )

        article = Article.objects.create(
            author=self.user,
            title="Has Image",
            excerpt="Excerpt with image",
            content="Body with image",
            status=Article.STATUS_DRAFT,
            is_published=False,
            featured_image=temp_img,
        )
        request = self.factory.get("/articles/")
        serializer = ArticleSerializer(instance=article, context={"request": request})
        data = serializer.data

        self.assertIn("featured_image_url", data)
        self.assertTrue(data["featured_image_url"].startswith("http://testserver"))


    def test_author_field_and_author_id_behavior(self):
        """
        - On serialization, `author` equals str(user), and `author_id` is absent.
        - On deserialization, passing `author_id` sets the correct user.
        """
        request = self.factory.get("/articles/")
        serializer = ArticleSerializer(instance=self.published_article, context={"request": request})
        data = serializer.data

        self.assertEqual(data["author"], str(self.user))
        self.assertNotIn("author_id", data)

        # Create a new article by other_user
        payload = {
            "author_id": self.other_user.id,
            "title": "Other's Article",
            "excerpt": "By other",
            "content": "Some content",
            "status": Article.STATUS_DRAFT,
            "is_published": False,
        }
        create_req = self.factory.post("/articles/")
        create_serial = ArticleSerializer(data=payload, context={"request": create_req})
        self.assertTrue(create_serial.is_valid(), create_serial.errors)
        new_article = create_serial.save()
        self.assertEqual(new_article.author, self.other_user)


    def test_validation_error_when_no_author_id_on_create(self):
        """
        Creating without `author_id` should raise a ValidationError under key 'author'.
        """
        payload = {
            "title": "Missing Author",
            "excerpt": "No author",
            "content": "No author content",
            "status": Article.STATUS_DRAFT,
            "is_published": False,
        }
        create_req = self.factory.post("/articles/")
        serializer = ArticleSerializer(data=payload, context={"request": create_req})
        self.assertFalse(serializer.is_valid())
        # Error should be keyed under 'author' because validate() checks for author_id
        self.assertIn("author", serializer.errors)


    def test_read_only_url_field_cannot_be_overwritten(self):
        """
        Passing a custom 'url' in input should not override the generated URL.
        """
        payload = {
            "author_id": self.user.id,
            "title": "Override URL",
            "excerpt": "Nope",
            "content": "Nope",
            "status": Article.STATUS_DRAFT,
            "is_published": False,
            "url": "http://malicious/override/",
        }
        create_req = self.factory.post("/articles/")
        serializer = ArticleSerializer(data=payload, context={"request": create_req})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        article = serializer.save()

        detail_url = reverse("article-detail", kwargs={"slug": article.slug})
        self.assertEqual(serializer.data["url"], f"http://testserver{detail_url}")


    def test_search_and_filter_fields_present_in_serializer_meta(self):
        """
        Confirm that Meta.fields contains the expected fields for filtering/searching.
        """
        meta_fields = ArticleSerializer.Meta.fields
        self.assertIn("status", meta_fields)
        self.assertIn("is_published", meta_fields)
        self.assertIn("title", meta_fields)
        self.assertIn("excerpt", meta_fields)
        self.assertIn("content", meta_fields)



# ---------- Test URLConf for HyperlinkedIdentityField ----------
router = DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [
    path("", include(router.urls)),
]



@override_settings(ROOT_URLCONF=__name__)
class VideoSerializerTests(TestCase):
    
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username="creator", email="creator@example.com", password="secret"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="password"
        )

        # API request factory
        self.factory = APIRequestFactory()

        # Draft video (no slug, embed_code, or published_at)
        self.draft_video = Video.objects.create(
            author=self.user,
            title="Draft Video",
            slug="",  # will be generated on save
            url="https://example.com/video.mp4",
            embed_code="",
            description="Draft description",
            status=Video.STATUS_DRAFT,
            is_published=False,
        )

        # Published video (slug auto, published_at set)
        self.published_video = Video.objects.create(
            author=self.user,
            title="Published Video",
            slug="",  # let save() generate
            url="https://example.com/vid.mp4",
            embed_code="",
            description="Published description",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )


    def test_serialize_video_fields(self):
        """
        Serializing an existing published video should include:
        - 'url' as hyperlinked identity to /videos/{slug}/
        - 'id', 'slug', 'author' (str), 'title', 'description', 'video url', 'embed_code', 
          'thumbnail_url' (None), 'duration', 'status', 'is_published', 'published_at',
          'created_at', 'updated_at'.
        - 'author_id' must NOT appear.
        """
        request = self.factory.get("/videos/")
        serializer = VideoSerializer(
            instance=self.published_video, context={"request": request}
        )
        data = serializer.data

        # Hyperlinked detail URL
        detail_url = reverse("video-detail", kwargs={"slug": self.published_video.slug})
        self.assertEqual(data["detail_url"], f"http://testserver{detail_url}")

        # ID and slug
        self.assertEqual(data["id"], self.published_video.id)
        self.assertEqual(data["slug"], self.published_video.slug)

        # Author string
        self.assertEqual(data["author"], str(self.user))

        # Core fields
        self.assertEqual(data["title"], "Published Video")
        self.assertEqual(data["description"], "Published description")
        self.assertEqual(data["detail_url"], f"http://testserver{detail_url}")  # hyperlink, not model URL
        self.assertEqual(data["embed_code"], "")
        self.assertIsNone(data["thumbnail_url"])

        # Duration default None
        self.assertIsNone(data["duration"])

        # Status / publication
        self.assertEqual(data["status"], Video.STATUS_PUBLISHED)
        self.assertTrue(data["is_published"])
        self.assertIsNotNone(data["published_at"])

        # Timestamps
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        # Write-only should not show
        self.assertNotIn("author_id", data)


    def test_deserialize_create_with_url_sets_slug_and_published_at(self):
        """
        Creating with only 'url' (no embed_code) and is_published=True should:
          - Validate because url present
          - Auto-generate slug from title
          - Auto-set published_at
        """
        payload = {
            "author_id": self.user.id,
            "title": "New Video",
            "description": "Some desc",
            "url": "https://example.com/new.mp4",
            "embed_code": "",
            "status": Video.STATUS_PUBLISHED,
            "is_published": True,
        }
        request = self.factory.post("/videos/")
        serializer = VideoSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        video = serializer.save()

        # Slug must start with 'new-video'
        self.assertTrue(video.slug.startswith("new-video"))

        # published_at auto-set
        self.assertIsNotNone(video.published_at)
        self.assertAlmostEqual(video.published_at, timezone.now(), delta=timedelta(seconds=5))

        # Author correctly set
        self.assertEqual(video.author, self.user)


    def test_deserialize_create_with_embed_only(self):
        """
        Creating with only 'embed_code' (no url) should also validate.
        """
        embed_html = "<iframe></iframe>"
        payload = {
            "author_id": self.user.id,
            "title": "Embed Video",
            "description": "Embed desc",
            "url": "",
            "embed_code": embed_html,
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        request = self.factory.post("/videos/")
        serializer = VideoSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        video = serializer.save()
        self.assertEqual(video.embed_code, embed_html)
        self.assertEqual(video.url, "")  # URL field stored as blank
        self.assertFalse(video.is_published)
        self.assertIsNone(video.published_at)


    def test_validation_requires_url_or_embed(self):
        """
        Attempt to create without url AND embed_code should raise ValidationError.
        """
        payload = {
            "author_id": self.user.id,
            "title": "Invalid Video",
            "description": "No media",
            "url": "",
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        request = self.factory.post("/videos/")
        serializer = VideoSerializer(data=payload, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)


    def test_update_toggle_publish_sets_published_at(self):
        """
        If updating draft->published without providing published_at, it must be set to now.
        """
        payload = {
            "is_published": True,
            "url": self.draft_video.url,   # supply the existing URL so validate() won’t fail
        }
        request = self.factory.patch(f"/videos/{self.draft_video.slug}/")
        serializer = VideoSerializer(
            instance=self.draft_video,
            data=payload,
            partial=True,
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertTrue(updated.is_published)
        self.assertIsNotNone(updated.published_at)
        self.assertGreaterEqual(updated.published_at, self.draft_video.created_at)


    def test_slug_and_read_only_ignored_on_update(self):
        """
        Passing 'slug', 'created_at', or 'updated_at' in update payload must be ignored.
        """
        original_slug = self.draft_video.slug
        orig_created = self.draft_video.created_at
        orig_updated = self.draft_video.updated_at

        future_time = (timezone.now() + timedelta(days=7)).isoformat()
        payload = {
            "slug": "fake-slug",
            "created_at": future_time,
            "updated_at": future_time,
            "title": "Modified Title",
            "url": self.draft_video.url  # include existing URL so validation passes
        }
        request = self.factory.put(f"/videos/{original_slug}/")
        serializer = VideoSerializer(
            instance=self.draft_video, data=payload, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        # Slug unchanged
        self.assertEqual(updated.slug, original_slug)
        # created_at unchanged
        self.assertEqual(updated.created_at, orig_created)
        # updated_at should be newer but not equal to fake future
        self.assertNotEqual(updated.updated_at, timezone.datetime.fromisoformat(future_time))
        self.assertGreaterEqual(updated.updated_at, orig_updated)

        # Title updated
        self.assertEqual(updated.title, "Modified Title")


    def test_thumbnail_url_included_if_thumbnail_present(self):
        """
        If thumbnail is uploaded, serializer must return absolute URL under 'thumbnail_url'.
        """
        # Create small in-memory GIF
        gif = (
            b"\x47\x49\x46\x38\x37\x61\x01\x00\x01\x00\x80\x00\x00\x00"
            b"\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        )
        temp_thumbnail = SimpleUploadedFile(
            name="thumb.gif",
            content=gif,
            content_type="image/gif"
        )
        video = Video.objects.create(
            author=self.user,
            title="Has Thumbnail",
            slug="",  # autogenerated
            url="https://example.com/x.mp4",
            embed_code="",
            description="Desc",
            status=Video.STATUS_DRAFT,
            is_published=False,
            thumbnail=temp_thumbnail
        )
        request = self.factory.get("/videos/")
        serializer = VideoSerializer(instance=video, context={"request": request})
        data = serializer.data

        self.assertIn("thumbnail_url", data)
        self.assertTrue(data["thumbnail_url"].startswith("http://testserver"))


    def test_author_field_and_author_id_behavior(self):
        """
        On serialization, 'author' equals str(user) and 'author_id' not shown.
        On creation, passing 'author_id' associates the correct user.
        """
        request = self.factory.get("/videos/")
        serializer = VideoSerializer(instance=self.published_video, context={"request": request})
        data = serializer.data

        self.assertEqual(data["author"], str(self.user))
        self.assertNotIn("author_id", data)

        # Create new video with other user
        payload = {
            "author_id": self.other.id,
            "title": "Other's Video",
            "description": "Some desc",
            "url": "https://example.com/other.mp4",
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        create_req = self.factory.post("/videos/")
        create_serial = VideoSerializer(data=payload, context={"request": create_req})
        self.assertTrue(create_serial.is_valid(), create_serial.errors)
        new_video = create_serial.save()
        self.assertEqual(new_video.author, self.other)


    def test_validation_error_when_no_author_id_on_create(self):
        """
        Creating without 'author_id' should yield ValidationError under 'author'.
        """
        payload = {
            "title": "No Author Video",
            "description": "Desc",
            "url": "https://example.com/noauthor.mp4",
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
        }
        create_req = self.factory.post("/videos/")
        serializer = VideoSerializer(data=payload, context={"request": create_req})
        self.assertFalse(serializer.is_valid())
        self.assertIn("author_id", serializer.errors)


    def test_read_only_url_field_cannot_be_overwritten(self):
        """
        Passing 'url' (hyperlinked field) in payload should not override hyperlink.
        """
        malicious_link = "http://malicious/override/"
        payload = {
            "author_id": self.user.id,
            "title": "Override URL Video",
            "description": "Desc",
            "url": "https://example.com/valid.mp4",  # valid model URL
            "embed_code": "",
            "status": Video.STATUS_DRAFT,
            "is_published": False,
            "detail_url": malicious_link,  # attempt to override hyperlink
        }
        create_req = self.factory.post("/videos/")
        serializer = VideoSerializer(data=payload, context={"request": create_req})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        video = serializer.save()

        expected_detail = reverse("video-detail", kwargs={"slug": video.slug})
        self.assertEqual(serializer.data["detail_url"], f"http://testserver{expected_detail}")
        # Also ensure model URL is stored correctly
        self.assertEqual(serializer.data["url"], "https://example.com/valid.mp4")


    def test_search_and_filter_fields_present_in_serializer_meta(self):
        """
        Confirm that expected fields for filtering/search appear in Meta.fields.
        """
        meta_fields = VideoSerializer.Meta.fields
        self.assertIn("status", meta_fields)
        self.assertIn("is_published", meta_fields)
        self.assertIn("title", meta_fields)
        self.assertIn("description", meta_fields)
        self.assertIn("url", meta_fields)



class ExerciseGuideSerializerTests(TestCase):

    def setUp(self):
        # Create a request factory for building absolute URIs
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        
        # Create a user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass"
        )
        
        # Create a sample ExerciseGuide with an image
        gif = (
            b"\x47\x49\x46\x38\x37\x61\x01\x00\x01\x00\x80\x00\x00\x00"
            b"\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        )
        self.image_file = SimpleUploadedFile(
            "test.gif", gif, content_type="image/gif"
        )
        self.guide = ExerciseGuide.objects.create(
            author=self.user,
            name="Push Up",
            excerpt="A basic upper-body exercise.",
            steps="1. Get into plank\n2. Lower your body\n3. Push back up",
            difficulty=ExerciseGuide.DIFFICULTY_BEGINNER,
            primary_muscle="Chest",
            equipment_required="None",
            image=self.image_file,
            video_embed="<iframe></iframe>",
        )


    def test_serialize_fields(self):
        """Serializer should include all read-only & writable fields correctly."""
        serializer = ExerciseGuideSerializer(
            instance=self.guide, context={"request": self.request}
        )
        data = serializer.data
        
        # Read-only hyperlinked identity
        self.assertIn("url", data)
        self.assertTrue(data["url"].endswith(f"/exercise-guides/{self.guide.slug}/"))
        
        # Core fields
        self.assertEqual(data["id"], self.guide.id)
        self.assertEqual(data["slug"], self.guide.slug)
        self.assertEqual(data["author"], str(self.user))
        self.assertEqual(data["name"], "Push Up")
        self.assertEqual(data["excerpt"], "A basic upper-body exercise.")
        self.assertEqual(data["steps"], "1. Get into plank\n2. Lower your body\n3. Push back up")
        self.assertEqual(data["difficulty"], ExerciseGuide.DIFFICULTY_BEGINNER)
        self.assertEqual(data["primary_muscle"], "Chest")
        self.assertEqual(data["equipment_required"], "None")
        self.assertEqual(data["video_embed"], "<iframe></iframe>")
        
        # Image URL is absolute
        self.assertIn("image_url", data)
        self.assertTrue(data["image_url"].startswith("http://testserver"))
        self.assertTrue(data["image_url"].endswith("/" + self.guide.image.name))
        
        # Timestamps
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        
        # Read-only: author_id should not appear
        self.assertNotIn("author_id", data)


    def test_validate_requires_author_on_create(self):
        """Creating without author_id should raise under 'author'."""
        payload = {
            "name": "Squat",
            "excerpt": "Lower-body exercise",
            "steps": "1. Stand\n2. Squat down\n3. Stand up",
            "difficulty": ExerciseGuide.DIFFICULTY_BEGINNER,
            "primary_muscle": "Legs",
            "equipment_required": "None",
            "video_embed": "",
        }
        serializer = ExerciseGuideSerializer(data=payload, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("author", serializer.errors)
        self.assertEqual(serializer.errors["author"][0], "This field is required.")


    def test_validate_rejects_empty_steps(self):
        """Creating or updating with blank steps should raise under 'steps'."""
        # Create with author_id but blank steps
        payload = {
            "author_id": self.user.id,
            "name": "Squat",
            "excerpt": "Lower-body",
            "steps": "   ",
            "difficulty": ExerciseGuide.DIFFICULTY_BEGINNER,
            "primary_muscle": "Legs",
            "equipment_required": "",
            "video_embed": "",
        }
        serializer = ExerciseGuideSerializer(data=payload, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("steps", serializer.errors)
        self.assertEqual(serializer.errors["steps"][0], "Exercise steps cannot be empty.")


    def test_create_success(self):
        """Valid data should create an ExerciseGuide with auto-generated slug."""
        payload = {
            "author_id": self.user.id,
            "name": "Lunge",
            "excerpt": "Another lower-body exercise",
            "steps": "1. Step forward\n2. Bend both knees\n3. Return",
            "difficulty": ExerciseGuide.DIFFICULTY_BEGINNER,
            "primary_muscle": "Legs",
            "equipment_required": "",
            "video_embed": "",
        }
        serializer = ExerciseGuideSerializer(data=payload, context={"request": self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        guide = serializer.save()

        # Slug auto-generated from name
        self.assertTrue(guide.slug.startswith("lunge"))
        self.assertEqual(guide.name, "Lunge")
        self.assertEqual(guide.author, self.user)


    def test_update_preserves_slug(self):
        """Updating name should not change an existing slug."""
        original_slug = self.guide.slug
        payload = {"name": "Push Up Advanced"}
        serializer = ExerciseGuideSerializer(
            instance=self.guide, data=payload, partial=True, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.slug, original_slug)
        self.assertEqual(updated.name, "Push Up Advanced")



class FitnessMeasurementSerializerTests(TestCase):

    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="pass")
        # A measurement instance
        self.measurement = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=180,
            weight_kg=81.0,
            gender=FitnessMeasurement.GENDER_MALE,
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),  # 30 years ago
        )
        self.factory = APIRequestFactory()


    def test_serialize_includes_fields_and_computed(self):
        """
        Serializer.data should include all model fields and computed properties.
        """
        request = self.factory.get("/measurements/{}/".format(self.measurement.pk))
        serializer = FitnessMeasurementSerializer(
            instance=self.measurement,
            context={"request": request}
        )
        data = serializer.data

        # URL field
        expected_url = request.build_absolute_uri(
            drf_reverse("fitnessmeasurement-detail", kwargs={"pk": self.measurement.pk}, request=request)
        )
        self.assertEqual(data["url"], expected_url)

        # Basic fields
        self.assertEqual(data["id"], self.measurement.pk)
        self.assertEqual(data["user"], str(self.user))
        self.assertNotIn("user_id", data)
        self.assertEqual(data["height_cm"], 180)
        self.assertEqual(data["weight_kg"], 81.0)
        self.assertEqual(data["gender"], FitnessMeasurement.GENDER_MALE)
        self.assertEqual(
            data["date_of_birth"],
            (timezone.now().date() - timedelta(days=365 * 30)).isoformat()
        )

        # Computed
        self.assertAlmostEqual(data["height_m"], 1.80, places=2)
        self.assertAlmostEqual(data["bmi"], round(81.0 / (1.8 * 1.8), 2))
        # BMI category at BMI=25 is Overweight
        self.assertEqual(data["bmi_category"], "Overweight")
        expected_bsa = round(math.sqrt((180 * 81.0) / 3600.0), 2)
        self.assertAlmostEqual(data["bsa"], expected_bsa)

        # Read-only timestamps present
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)


    def test_deserialize_valid_input_creates_instance(self):
        """
        Valid input with user_id should create a new FitnessMeasurement.
        """
        payload = {
            "user_id": self.user.pk,
            "height_cm": 170,
            "weight_kg": 70.5,
            "gender": FitnessMeasurement.GENDER_FEMALE,
            "date_of_birth": (date.today() - timedelta(days=365 * 25)).isoformat(),
        }
        request = self.factory.post("/measurements/", payload, format="json")
        serializer = FitnessMeasurementSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        inst = serializer.save()

        self.assertEqual(inst.user, self.user)
        self.assertEqual(inst.height_cm, 170)
        self.assertEqual(inst.weight_kg, 70.5)
        self.assertEqual(inst.gender, FitnessMeasurement.GENDER_FEMALE)
        self.assertEqual(inst.date_of_birth, date.today() - timedelta(days=365 * 25))


    def test_validate_height_cm_must_be_positive(self):
        payload = {"user_id": self.user.pk, "height_cm": 0, "weight_kg": 60.0}
        serializer = FitnessMeasurementSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("height_cm", serializer.errors)
        self.assertEqual(serializer.errors["height_cm"][0], "Height must be a positive integer.")


    def test_validate_weight_kg_must_be_positive(self):
        payload = {"user_id": self.user.pk, "height_cm": 160, "weight_kg": 0}
        serializer = FitnessMeasurementSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("weight_kg", serializer.errors)
        self.assertEqual(serializer.errors["weight_kg"][0], "Weight must be a positive number.")


    def test_validate_date_of_birth_in_past(self):
        tomorrow = date.today() + timedelta(days=1)
        payload = {"user_id": self.user.pk, "height_cm": 160, "weight_kg": 60.0, "date_of_birth": tomorrow.isoformat()}
        serializer = FitnessMeasurementSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_of_birth", serializer.errors)
        self.assertEqual(serializer.errors["date_of_birth"][0], "Date of birth must be in the past.")


    def test_requires_user_id_on_create(self):
        payload = {"height_cm": 160, "weight_kg": 60.0}
        serializer = FitnessMeasurementSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)
