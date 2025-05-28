from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from content.models import Article, Video



class ArticleModelTests(TestCase):

    def setUp(self):
        self.now = timezone.now()

        # Create a draft article (no slug, not published)
        self.draft = Article.objects.create(
            title="My First Article",
            slug="",                # should be auto‐generated in save()
            author=None,
            excerpt="Just an excerpt",
            content="The full body goes here.",
            is_published=False,
            status=Article.STATUS_DRAFT,
        )


    def test___str__returns_title(self):
        self.assertEqual(str(self.draft), "My First Article")


    def test_slug_auto_generated_on_save(self):
        # After setUp, slug was blank—save() should have generated it
        self.assertTrue(self.draft.slug)
        self.assertTrue(self.draft.slug.startswith(slugify("My First Article")))


    def test_slug_collision_appends_counter(self):
        # Create another with identical title → collision
        other = Article(
            title=self.draft.title,
            slug="",
            excerpt="X",
            content="Y",
            is_published=False,
            status=Article.STATUS_DRAFT,
        )
        other.save()

        # Should not match the first slug exactly
        self.assertNotEqual(other.slug, self.draft.slug)
        # Should begin with the same base
        base = slugify(self.draft.title)
        self.assertTrue(other.slug.startswith(base))


    def test_clean_requires_published_at_when_published(self):
        art = Article(
            title="Publishing Now",
            slug="",
            excerpt="E",
            content="C",
            is_published=True,
            status=Article.STATUS_PUBLISHED,
            published_at=None,   # missing
        )
        with self.assertRaises(ValidationError) as cm:
            art.full_clean()
        self.assertIn("published_at must be set", str(cm.exception))


    def test_save_sets_published_at_if_missing(self):
        art = Article(
            title="Set Published At",
            slug="",
            excerpt="E",
            content="C",
            is_published=True,
            status=Article.STATUS_PUBLISHED,
            published_at=None,
        )
        art.save()
        self.assertIsNotNone(art.published_at)
        # It should be very close to “now”
        self.assertTrue(timezone.now() - art.published_at < timedelta(seconds=1))


    def test_published_manager_filters_only_published(self):
        # Initially, only the draft exists, so published manager is empty
        self.assertEqual(Article.published.count(), 0)

        # Publish the draft
        self.draft.is_published = True
        self.draft.status = Article.STATUS_PUBLISHED
        self.draft.published_at = timezone.now()
        self.draft.save()

        self.assertEqual(Article.published.count(), 1)
        self.assertIn(self.draft, Article.published.all())


    def test_default_manager_returns_all(self):
        # Whatever’s in published should be a subset of all objects
        total = Article.objects.count()
        published = Article.published.count()
        self.assertGreaterEqual(total, published)


    def test_get_absolute_url_contains_slug(self):
        url = self.draft.get_absolute_url()
        self.assertIsInstance(url, str)
        self.assertIn(self.draft.slug, url)
        # We won’t attempt to resolve against URLconf here—just ensure it’s well‐formed
        self.assertTrue(url.endswith(f"/{self.draft.slug}/") or self.draft.slug in url)



class VideoModelTests(TestCase):
    
    def setUp(self):
        # Create a draft video without slug or published_at; URL only
        self.draft = Video.objects.create(
            title="Mystery Video!",
            slug="",                    # triggers auto-slug
            url="https://youtu.be/abc123",
            embed_code="",              # OK because URL is present
            description="A test video.",
            status=Video.STATUS_DRAFT,
            is_published=False,         # draft state
        )


    def test_str_returns_title(self):
        self.assertEqual(str(self.draft), "Mystery Video!")


    def test_slug_auto_generated_on_save(self):
        expected_base = slugify(self.draft.title)
        self.assertTrue(self.draft.slug)
        self.assertEqual(self.draft.slug, expected_base)


    def test_slug_collision_appends_counter(self):
        # Title with same slug base → collision
        other = Video.objects.create(
            title="Mystery Video?",
            slug="",
            url="http://example.com/watch",
            embed_code="",
            description="Another test.",
            status=Video.STATUS_DRAFT,
            is_published=False,
        )
        base = slugify(self.draft.title)
        self.assertTrue(other.slug.startswith(base))
        self.assertNotEqual(other.slug, self.draft.slug)


    def test_clean_requires_published_at_when_published(self):
        v = Video(
            title="Now Live",
            slug="",
            url="http://example.com",
            embed_code="",               # embed_code blank but URL present
            description="Should be published.",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=None,           # missing timestamp
        )
        with self.assertRaises(ValidationError) as cm:
            v.full_clean()
        self.assertIn(
            "published_at must be set when is_published=True",
            str(cm.exception)
        )


    def test_clean_requires_url_or_embed_code(self):
        v = Video(
            title="No Source",
            slug="",
            url="",                      # neither URL...
            embed_code="",               # ...nor embed_code
            description="Missing both URL and embed.",
            status=Video.STATUS_DRAFT,
            is_published=False,
        )
        with self.assertRaises(ValidationError) as cm:
            v.full_clean()
        self.assertIn(
            "Provide either a URL or embed code for the video",
            str(cm.exception)
        )


    def test_save_auto_sets_published_at(self):
        # Create with is_published True but no published_at
        v = Video.objects.create(
            title="Publish Now",
            slug="",
            url="http://example.com",
            embed_code="",
            description="Immediate publish.",
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=None,
        )
        # After save, published_at must be populated
        self.assertIsNotNone(v.published_at)
        self.assertTrue(timezone.now() - v.published_at < timedelta(seconds=1))


    def test_published_manager_filters_only_published(self):
        # Initially draft, so published manager returns no entries
        self.assertEqual(Video.published.count(), 0)

        # Mark draft as published
        self.draft.is_published = True
        self.draft.status = Video.STATUS_PUBLISHED
        self.draft.published_at = timezone.now()
        self.draft.save()

        self.assertEqual(Video.published.count(), 1)
        self.assertIn(self.draft, Video.published.all())


    def test_default_manager_returns_all(self):
        total = Video.objects.count()
        published = Video.published.count()
        self.assertGreaterEqual(total, published)


    def test_get_absolute_url_fallback(self):
        """
        Since no 'content:video-detail' namespace exists in tests,
        get_absolute_url should return the fallback path.
        """
        url = self.draft.get_absolute_url()
        expected = f"/videos/{self.draft.slug}/"
        self.assertEqual(url, expected)
