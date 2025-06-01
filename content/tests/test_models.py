import math
from datetime import timedelta, date

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.urls import NoReverseMatch, reverse

from content.models import Article, Video, ExerciseGuide, FitnessMeasurement
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



class FitnessMeasurementModelTests(TestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        # A known past date for date_of_birth tests
        self.past_date = timezone.now().date() - timedelta(days=365 * 25)  # 25 years ago


    def test_str_contains_user_height_weight_and_date(self):
        """
        __str__ should include username, height_cm, weight_kg, and the date portion of created_at.
        """
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=175,
            weight_kg=70.0,
        )
        text = str(m)
        # It should contain username
        self.assertIn(self.user.username, text)
        # It should contain height and weight
        self.assertIn("175cm", text)
        self.assertIn("70.0kg", text)
        # It should contain the created date (YYYY-MM-DD)
        created_str = m.created_at.date().isoformat()
        self.assertIn(created_str, text)


    def test_height_m_property(self):
        """
        height_m should return height_cm divided by 100.
        """
        m = FitnessMeasurement(user=self.user, height_cm=180, weight_kg=75.0)
        # Without saving, height_m still works
        self.assertEqual(m.height_m, 1.80)
        # Even if height_cm changes
        m.height_cm = 150
        self.assertEqual(m.height_m, 1.50)


    def test_bmi_computation_and_rounding(self):
        """
        BMI = weight_kg / (height_m ** 2), rounded to two decimals.
        """
        # height: 180 cm -> 1.8 m; weight: 80 kg -> BMI = 80 / (1.8^2) = 24.691...
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=180,
            weight_kg=80.0,
        )
        expected_bmi = round(80.0 / (1.8 * 1.8), 2)
        self.assertAlmostEqual(m.bmi, expected_bmi)
        # If height_m is zero (invalid), bmi property should return 0.0
        m_zero = FitnessMeasurement(user=self.user, height_cm=0, weight_kg=50.0)
        # Manually set height_cm to zero and call bmi
        m_zero.height_cm = 0
        self.assertEqual(m_zero.height_m, 0.0)
        self.assertEqual(m_zero.bmi, 0.0)


    def test_bmi_category_ranges(self):
        """
        Given a BMI, bmi_category should map to WHO categories.
        """
        # Underweight: BMI < 18.5
        m1 = FitnessMeasurement(
            user=self.user, height_cm=170, weight_kg=50.0
        )  # 50 / (1.7^2) ≈ 17.30
        self.assertEqual(m1.bmi_category, "Underweight")

        # Normal weight: 18.5 <= BMI < 25
        m2 = FitnessMeasurement(
            user=self.user, height_cm=170, weight_kg=65.0
        )  # ≈22.49
        self.assertEqual(m2.bmi_category, "Normal weight")

        # Overweight: 25 <= BMI < 30
        m3 = FitnessMeasurement(
            user=self.user, height_cm=170, weight_kg=77.0
        )  # ≈26.64
        self.assertEqual(m3.bmi_category, "Overweight")

        # Obese: BMI >= 30
        m4 = FitnessMeasurement(
            user=self.user, height_cm=160, weight_kg=90.0
        )  # ≈35.16
        self.assertEqual(m4.bmi_category, "Obese")


    def test_bsa_computation(self):
        """
        BSA (Mosteller formula) = sqrt((height_cm * weight_kg) / 3600), rounded to two decimals.
        """
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=180,
            weight_kg=80.0,
        )
        expected_bsa = round(math.sqrt((180 * 80.0) / 3600.0), 2)
        self.assertAlmostEqual(m.bsa, expected_bsa)

        m2 = FitnessMeasurement(user=self.user, height_cm=0, weight_kg=0)
        # 0/3600 = 0, sqrt(0) = 0, rounded = 0.0
        m2.height_cm = 0
        m2.weight_kg = 0.0
        self.assertEqual(m2.bsa, 0.0)


    def test_clean_rejects_nonpositive_height(self):
        """
        clean() should raise ValidationError if height_cm <= 0.
        """
        m = FitnessMeasurement(user=self.user, height_cm=0, weight_kg=60.0)
        with self.assertRaises(ValidationError) as cm:
            m.full_clean()
        self.assertIn("height_cm", cm.exception.message_dict)
        self.assertIn("positive integer", cm.exception.message_dict["height_cm"][0])


    def test_clean_rejects_nonpositive_weight(self):
        """
        clean() should raise ValidationError if weight_kg <= 0.
        """
        m = FitnessMeasurement(user=self.user, height_cm=170, weight_kg=0.0)
        with self.assertRaises(ValidationError) as cm:
            m.full_clean()
        self.assertIn("weight_kg", cm.exception.message_dict)
        self.assertIn("positive number", cm.exception.message_dict["weight_kg"][0])


    def test_clean_rejects_date_of_birth_in_future_or_today(self):
        """
        clean() should raise if date_of_birth is today or in the future.
        """
        # Case 1: date_of_birth == today
        today = timezone.now().date()
        m1 = FitnessMeasurement(
            user=self.user,
            height_cm=170,
            weight_kg=60.0,
            date_of_birth=today
        )
        with self.assertRaises(ValidationError) as cm1:
            m1.full_clean()
        # error_dict["date_of_birth"][0] should now be a plain string containing "in the past"
        err_msg1 = cm1.exception.error_dict["date_of_birth"][0]
        self.assertIn("Date of birth must be in the past.", err_msg1)

        # Case 2: date_of_birth in the future
        tomorrow = today + timedelta(days=1)
        m2 = FitnessMeasurement(
            user=self.user,
            height_cm=170,
            weight_kg=60.0,
            date_of_birth=tomorrow
        )
        with self.assertRaises(ValidationError) as cm2:
            m2.full_clean()
        err_msg2 = cm2.exception.error_dict["date_of_birth"][0]
        self.assertIn("Date of birth must be in the past.", err_msg2)


    def test_get_absolute_url_fallbacks_to_pk(self):
        """
        If no named URL 'fitness:measurement-detail' exists,
        get_absolute_url() should return '/fitness/<pk>/'.
        """
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=165,
            weight_kg=55.0,
        )
        # Attempt to reverse; expecting NoReverseMatch inside, so fallback
        url = m.get_absolute_url()
        expected = f"/fitness/{m.pk}/"
        self.assertEqual(url, expected)


    def test_created_at_and_updated_at_auto_set(self):
        """
        Ensure that created_at and updated_at are automatically populated.
        """
        before = timezone.now()
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=180,
            weight_kg=80.0,
        )
        self.assertIsNotNone(m.created_at)
        self.assertIsNotNone(m.updated_at)
        # Both timestamps should be >= the moment before creation
        self.assertGreaterEqual(m.created_at, before)
        self.assertGreaterEqual(m.updated_at, before)


    def test_updating_record_updates_updated_at(self):
        """
        Changing a record and saving it again should update updated_at.
        """
        m = FitnessMeasurement.objects.create(
            user=self.user,
            height_cm=170,
            weight_kg=60.0,
        )
        original_updated = m.updated_at
        # Sleep a fraction to ensure a later timestamp (optional)
        m.weight_kg = 62.0
        m.save()
        self.assertGreater(m.updated_at, original_updated)
