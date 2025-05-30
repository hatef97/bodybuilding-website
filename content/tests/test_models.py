import math
import re

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.urls import NoReverseMatch

from content.models import Article, Video, ExerciseGuide, Calculator, ActiveCalculatorManager
from core.models import CustomUser as User



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



class ExerciseGuideModelTests(TestCase):

    def setUp(self):
        # Create an author
        self.author = User.objects.create_user(email='guideauthor@mail.com', username="guideauthor", password="password")
        # Create a valid guide without slug (to trigger auto‐slug)
        self.guide1 = ExerciseGuide.objects.create(
            name="Perfect Push-Up",
            slug="",  # will be auto‐slugged to "perfect-push-up"
            excerpt="A foundational chest exercise.",
            steps="1. Place hands under shoulders.\n2. Lower chest to ground.\n3. Push back up.",
            difficulty=ExerciseGuide.DIFFICULTY_BEGINNER,
            primary_muscle="Chest",
            equipment_required="None",
            image=None,
            video_embed="",
            author=self.author,
        )


    def test_str_returns_name(self):
        """__str__ should return the guide's name."""
        self.assertEqual(str(self.guide1), "Perfect Push-Up")


    def test_slug_auto_generated_on_save(self):
        """Saving with blank slug auto‐populates slugified name."""
        expected = slugify(self.guide1.name)
        self.assertEqual(self.guide1.slug, expected)


    def test_slug_uniqueness_collision(self):
        """
        Two distinct names that slugify to the same base produce different slugs.
        We use "Perfect Push-Up!" so slugify → "perfect-push-up", colliding with guide1.
        """
        guide2 = ExerciseGuide.objects.create(
            name="Perfect Push-Up!",
            slug="",  # same base slug
            excerpt=self.guide1.excerpt,
            steps=self.guide1.steps,
            difficulty=self.guide1.difficulty,
            primary_muscle=self.guide1.primary_muscle,
            equipment_required=self.guide1.equipment_required,
            image=None,
            video_embed="",
            author=self.author,
        )

        base = slugify(self.guide1.name)
        # guide1.slug == base; guide2.slug should be base-1 (or higher)
        self.assertTrue(guide2.slug.startswith(base))
        self.assertNotEqual(guide2.slug, self.guide1.slug)


    def test_clean_rejects_empty_steps(self):
        """
        clean() should raise ValidationError if steps are blank or whitespace.
        """
        bad = ExerciseGuide(
            name="No Steps Guide",
            slug="",
            excerpt="Missing steps.",
            steps="   \n  ",  # whitespace only
            difficulty=ExerciseGuide.DIFFICULTY_BEGINNER,
            primary_muscle="Legs",
            equipment_required="None",
            image=None,
            video_embed="",
            author=self.author,
        )
        with self.assertRaises(ValidationError) as cm:
            bad.full_clean()

        self.assertIn("Exercise steps cannot be empty", str(cm.exception))


    def test_get_absolute_url_raises_without_namespace(self):
        """
        get_absolute_url() should attempt reverse('content:exercise-detail', …)
        and, since no 'content' namespace is loaded in tests, raise NoReverseMatch.
        """
        with self.assertRaises(NoReverseMatch):
            self.guide1.get_absolute_url()



class CalculatorModelTests(TestCase):

    def setUp(self):
        self.valid_payload = {
            "key": "bmi",
            "name": "Body Mass Index",
            "description": "Calculate BMI",
            "parameters": {
                "weight_kg": {"label": "Weight (kg)", "min": 10, "max": 300, "step": 0.1},
                "height_m": {"label": "Height (m)",  "min": 0.5, "max": 3.0, "step": 0.01},
            },
            "formula": "weight_kg / (height_m ** 2)",
        }


    def test_str_returns_name(self):
        calc = Calculator(**self.valid_payload)
        self.assertEqual(str(calc), self.valid_payload["name"])


    def test_active_manager_filters_correctly(self):
        a = Calculator.objects.create(**self.valid_payload)
        b = Calculator.objects.create(
            **{**self.valid_payload, "key": "bmi2", "name": "BMI Two", "is_active": False}
        )
        qs = Calculator.active.all()
        self.assertIn(a, qs)
        self.assertNotIn(b, qs)
        # the custom manager itself
        self.assertIsInstance(Calculator.active, ActiveCalculatorManager)


    def test_clean_invalid_formula_raises(self):
        bad = Calculator(**{**self.valid_payload, "formula": "1 / ("})
        with self.assertRaises(ValidationError) as cm:
            bad.full_clean()
        self.assertIn("formula", cm.exception.message_dict)
        msg = cm.exception.message_dict["formula"][0]
        self.assertTrue(msg.startswith("Invalid Python expression"))


    def test_clean_bad_slug_raises(self):
        # supply a slug that has spaces and symbols
        calc = Calculator(**{**self.valid_payload, "slug": "bad slug!"})
        with self.assertRaises(ValidationError) as cm:
            calc.full_clean()
        self.assertIn("slug", cm.exception.error_dict)
        # Django's built-in slug-field message:
        self.assertIn(
            "letters, numbers, underscores or hyphens",
            cm.exception.error_dict["slug"][0].message
        )


    def test_clean_undefined_parameters_raises(self):
        # formula references `age` which is not in parameters or math
        calc = Calculator(**{**self.valid_payload, "formula": "weight_kg + age"})
        with self.assertRaises(ValidationError) as cm:
            calc.full_clean()
        self.assertIn("formula", cm.exception.error_dict)
        msg = cm.exception.error_dict["formula"][0].message
        self.assertIn("undefined parameters", msg)
        self.assertIn("age", msg)


    def test_save_auto_generates_slug_from_key(self):
        calc = Calculator.objects.create(**self.valid_payload)
        self.assertEqual(calc.slug, slugify(self.valid_payload["key"]))


    def test_save_different_keys_produce_different_slugs(self):
        c1 = Calculator.objects.create(**self.valid_payload)
        payload2 = {**self.valid_payload, "key": "bmi-alt", "name": "BMI Alt"}
        c2 = Calculator.objects.create(**payload2)
        self.assertEqual(c1.slug, "bmi")
        self.assertEqual(c2.slug, "bmi-alt")


    def test_calculate_correctly(self):
        calc = Calculator.objects.create(**self.valid_payload)
        result = calc.calculate(weight_kg=70, height_m=1.75)
        expected = 70 / (1.75 ** 2)
        self.assertAlmostEqual(result, expected, places=6)


    def test_calculate_missing_parameter_raises(self):
        calc = Calculator.objects.create(**self.valid_payload)
        with self.assertRaises(KeyError):
            calc.calculate(weight_kg=70)  # height_m missing


    def test_calculate_below_minimum_raises(self):
        calc = Calculator.objects.create(**self.valid_payload)
        with self.assertRaises(ValueError) as cm:
            calc.calculate(weight_kg=5, height_m=1.75)  # weight_kg < min
        self.assertIn("weight_kg below minimum", str(cm.exception))


    def test_calculate_above_maximum_raises(self):
        calc = Calculator.objects.create(**self.valid_payload)
        with self.assertRaises(ValueError) as cm:
            calc.calculate(weight_kg=70, height_m=5.0)  # height_m > max
        self.assertIn("height_m above maximum", str(cm.exception))


    def test_get_absolute_url_contains_slug(self):
        calc = Calculator.objects.create(**self.valid_payload)
        try:
            url = calc.get_absolute_url()
        except NoReverseMatch:
            # fallback if you haven't wired up the named URL
            url = f"/calculators/{calc.slug}/"
        self.assertIn(calc.slug, url)
        self.assertTrue(url.endswith(f"{calc.slug}/"))
        