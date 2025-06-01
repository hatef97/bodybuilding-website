from datetime import timedelta
import math

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.core.validators import URLValidator
from django.utils import timezone
from django.utils.text import slugify



class PublishedManager(models.Manager):
    """Custom manager to retrieve only published articles."""
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)



class Article(models.Model):
    """Blog article with rich metadata, slug support, and publication workflow."""

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    # Allow duplicate titles so we can test slug‐collision logic:
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-friendly identifier. Auto-generated from title if blank."
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        help_text="The user who wrote this article."
    )
    excerpt = models.TextField(
        blank=True,
        help_text="Short summary or teaser (shown on listings)."
    )
    content = models.TextField(
        help_text="Full article body (Markdown or HTML)."
    )

    featured_image = models.ImageField(
        upload_to='articles/featured/',
        blank=True, null=True,
        help_text="Optional banner image."
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text="Publishing state."
    )
    is_published = models.BooleanField(
        default=False,
        help_text="If true, article is publicly visible."
    )
    published_at = models.DateTimeField(
        blank=True, null=True,
        help_text="Date/time when the article went live."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()        # Default manager
    published = PublishedManager()    # Only is_published=True

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['slug']),
        ]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.title

    def clean(self):
        # Enforce that a published article has a published_at date.
        if self.is_published and not self.published_at:
            raise ValidationError("published_at must be set when is_published=True.")

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing, avoid collisions.
        if not self.slug:
            base = slugify(self.title)[:200]
            slug_candidate = base
            counter = 1
            while Article.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base}-{counter}"
                counter += 1
            self.slug = slug_candidate

        # If publishing now but no timestamp, set published_at
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return the URL for front-end article detail.
        Falls back to a simple '/articles/<slug>/' if no named route exists.
        """
        try:
            # Adjust this name to match your URLconf if needed
            return reverse('article-detail', kwargs={'slug': self.slug})
        except NoReverseMatch:
            return f"/articles/{self.slug}/"



class PublishedVideoManager(models.Manager):
    """Manager returning only published videos."""
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)



class Video(models.Model):
    """
    Video tutorial or guide.
    Supports external URLs or embedded media, thumbnail, author, and publish workflow.
    """

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="Auto-generated from title if left blank."
    )

    # Either an external link or embed code
    url = models.URLField(
        validators=[URLValidator()],
        help_text="URL to the video (e.g. YouTube/Vimeo link).",
    )
    embed_code = models.TextField(
        blank=True,
        help_text="Alternative embed HTML (if needed)."
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description or transcript (Markdown/HTML)."
    )
    thumbnail = models.ImageField(
        upload_to='videos/thumbnails/',
        blank=True,
        null=True,
        help_text="Optional thumbnail image."
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='videos',
        help_text="Creator of this video."
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text="Draft vs Published status."
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Controls public visibility."
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when video was published."
    )

    duration = models.DurationField(
        blank=True,
        null=True,
        help_text="Video length (optional)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    published = PublishedVideoManager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['slug']),
        ]
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def __str__(self):
        return self.title

    def clean(self):
        # Ensure slug uniqueness is handled by save
        # Ensure published_at is set if published
        if self.is_published and not self.published_at:
            raise ValidationError("published_at must be set when is_published=True.")
        if not (self.url or self.embed_code):
            raise ValidationError("Provide either a URL or embed code for the video.")

    def save(self, *args, **kwargs):
        # Auto-generate a unique slug if missing
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base
            n = 1
            while Video.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # Auto-set published_at when publishing
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns the front-end URL for this video.
        Assumes a named route 'content:video-detail' expecting a slug.
        """
        try:
            return reverse('content:video-detail', kwargs={'slug': self.slug})
        except NoReverseMatch:
            return f"/videos/{self.slug}/"


class ExerciseGuide(models.Model):
    """
    Step-by-step exercise guide.
    Supports auto-slugging, categorization, difficulty levels, images, and embedded video.
    """

    DIFFICULTY_BEGINNER = 'beginner'
    DIFFICULTY_INTERMEDIATE = 'intermediate'
    DIFFICULTY_ADVANCED = 'advanced'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, 'Beginner'),
        (DIFFICULTY_INTERMEDIATE, 'Intermediate'),
        (DIFFICULTY_ADVANCED, 'Advanced'),
    ]

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="Auto-generated from name if left blank."
    )

    excerpt = models.TextField(
        blank=True,
        help_text="Short summary or teaser shown in listings."
    )
    steps = models.TextField(
        help_text="Detailed, ordered steps (Markdown or HTML)."
    )

    difficulty = models.CharField(
        max_length=12,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_BEGINNER,
        db_index=True,
        help_text="Skill level required."
    )

    primary_muscle = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary muscle group (e.g. 'Chest', 'Legs')."
    )
    equipment_required = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated list of equipment, if any."
    )

    image = models.ImageField(
        upload_to='exercise_guides/',
        blank=True,
        null=True,
        help_text="Optional illustrative image."
    )
    video_embed = models.TextField(
        blank=True,
        help_text="Optional embed HTML (YouTube, Vimeo, etc.)."
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='exercise_guides',
        help_text="User who created this guide."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['difficulty']),
        ]
        verbose_name = "Exercise Guide"
        verbose_name_plural = "Exercise Guides"

    def __str__(self):
        return self.name

    def clean(self):
        # Slug will be auto-generated in save(), but ensure steps are non-empty:
        if not self.steps.strip():
            raise ValidationError("Exercise steps cannot be empty.")

    def save(self, *args, **kwargs):
        # Auto-slug from name
        if not self.slug:
            base = slugify(self.name)[:200]
            slug = base
            n = 1
            while ExerciseGuide.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns the URL to view this guide.
        Assumes a named URL 'content:exercise-detail' expecting a slug.
        """
        return reverse('content:exercise-detail', kwargs={'slug': self.slug})


class FitnessMeasurement(models.Model):
    """
    A simple record of a user's height & weight at a point in time.
    Auto‐computed properties:
      1. BMI = weight_kg / (height_m ** 2)
      2. BSA (Mosteller) = sqrt((height_cm * weight_kg) / 3600)
    """

    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fitness_measurements",
        help_text="Which user this measurement belongs to."
    )

    # Height in centimeters (must be positive)
    height_cm = models.PositiveIntegerField(
        help_text="Height in centimeters. (e.g. 175)"
    )

    # Weight in kilograms (must be positive, can include decimals)
    weight_kg = models.FloatField(
        help_text="Weight in kilograms. (e.g. 70.5)"
    )

    # Optional: gender and date_of_birth
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        help_text="Optional: needed for some body‐fat or BMR calculations."
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Optional: needed for age‐dependent calculators (e.g. BMR)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fitness Measurement"
        verbose_name_plural = "Fitness Measurements"

    def __str__(self):
        return f"{self.user.username} @ {self.height_cm}cm / {self.weight_kg}kg (on {self.created_at.date()})"

    def clean(self):
        """
        Ensure height_cm and weight_kg are positive.
        If date_of_birth is set, it must be strictly in the past (not today or future).
        """
        errors = {}

        # 1) height_cm must be > 0
        if self.height_cm <= 0:
            # Use a list of strings so that error_dict[...] is a list of strings
            errors["height_cm"] = ["Height must be a positive integer."]

        # 2) weight_kg must be > 0
        if self.weight_kg <= 0:
            errors["weight_kg"] = ["Weight must be a positive number."]

        # 3) date_of_birth, if provided, must be strictly before today
        if self.date_of_birth:
            comparison_date = timezone.now().date()
            if self.date_of_birth >= comparison_date:
                errors["date_of_birth"] = ["Date of birth must be in the past."]

        if errors:
            # Passing a dict of (field → list_of_strings) yields
            # error_dict[field] == list_of_strings, so [0] is exactly the plain string.
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Before saving, ensure that updated_at always moves forward by at least one second.
        """
        if self.pk:
            old = FitnessMeasurement.objects.filter(pk=self.pk).first()
            if old:
                now = timezone.now()
                if now <= old.updated_at:
                    bumped = old.updated_at + timedelta(seconds=1)
                    self.updated_at = bumped
                else:
                    self.updated_at = now

        super().save(*args, **kwargs)

    @property
    def height_m(self) -> float:
        """Convert height_cm to meters."""
        return self.height_cm / 100.0

    @property
    def bmi(self) -> float:
        """
        BMI = weight_kg / (height_m)^2, rounded to two decimals.
        If height_m is zero, return 0.0.
        """
        h = self.height_m
        if h <= 0:
            return 0.0
        return round(self.weight_kg / (h * h), 2)

    @property
    def bmi_category(self) -> str:
        """
        Return a WHO category string based on BMI value.
        """
        val = self.bmi
        if val < 18.5:
            return "Underweight"
        if val < 25:
            return "Normal weight"
        if val < 30:
            return "Overweight"
        return "Obese"

    @property
    def bsa(self) -> float:
        """
        Body Surface Area (Mosteller formula) = sqrt((height_cm * weight_kg) / 3600)
        Rounded to two decimals.
        """
        return round(math.sqrt((self.height_cm * self.weight_kg) / 3600.0), 2)

    def get_absolute_url(self):
        """
        Since there’s no named URL pattern, fallback to "/fitness/<pk>/".
        """
        return f"/fitness/{self.pk}/"
