import math

from django.conf import settings
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
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
            raise models.ValidationError("Exercise steps cannot be empty.")

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



class ActiveCalculatorManager(models.Manager):
    """Manager returning only active calculators."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)



class Calculator(models.Model):
    """
    Defines a fitness calculator (BMI, Body Fat, etc.) with:
    - name & slug for URLs
    - parameter schema in JSONField
    - a Python 'formula' expression evaluated at runtime
    """

    key = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier, e.g. 'bmi', 'body_fat'."
    )
    name = models.CharField(
        max_length=100,
        help_text="Human–readable name, e.g. 'Body Mass Index (BMI)'."
    )
    slug = models.SlugField(
        max_length=60,
        unique=True,
        blank=True,
        help_text="Auto–generated from key or name if blank."
    )

    description = models.TextField(
        blank=True,
        help_text="Explain what this calculator does."
    )

    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Schema for inputs, e.g.:\n"
            "{ 'weight_kg': {'label':'Weight (kg)','min':30,'max':300,'step':0.1},\n"
            "  'height_m': {'label':'Height (m)','min':1.0,'max':2.5,'step':0.01} }\n"
        )
    )

    formula = models.TextField(
        help_text=(
            "Python expression using parameter names, e.g.:\n"
            "'weight_kg / (height_m ** 2)'"
        )
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to disable this calculator."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    active = ActiveCalculatorManager()

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['key']),
        ]
        verbose_name = "Calculator"
        verbose_name_plural = "Calculators"

    def __str__(self):
        return self.name

    def clean(self):
        # Ensure formula can be compiled
        try:
            compile(self.formula, '<formula>', 'eval')
        except Exception as e:
            raise ValidationError({'formula': f"Invalid Python expression: {e}"})

        # Slug integrity
        if self.slug and self.slug != slugify(self.slug):
            raise ValidationError({'slug': "Slug must be URL-friendly (letters, numbers, hyphens)."})

        # Parameter keys match formula variables
        import re
        var_names = set(re.findall(r'\b[a-zA-Z_]\w*\b', self.formula))
        missing = var_names - set(self.parameters.keys()) - set(dir(math))
        if missing:
            raise ValidationError({
                'formula': f"Formula refers to undefined parameters: {', '.join(missing)}"
            })

    def save(self, *args, **kwargs):
        # Auto–slug from key if missing
        if not self.slug:
            base = slugify(self.key)[:55]
            slug = base
            n = 1
            while Calculator.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def calculate(self, **inputs):
        """
        Evaluate the formula with given inputs.
        - Only math module and provided inputs are in scope.
        - Raises KeyError or ValueError on missing/invalid inputs.
        """
        # Validate inputs
        for name, schema in self.parameters.items():
            if name not in inputs:
                raise KeyError(f"Missing parameter: {name}")
            val = inputs[name]
            minv = schema.get('min')
            maxv = schema.get('max')
            if minv is not None and val < minv:
                raise ValueError(f"{name} below minimum {minv}")
            if maxv is not None and val > maxv:
                raise ValueError(f"{name} above maximum {maxv}")

        # Safe evaluation context
        safe_locals = {**{k: inputs[k] for k in self.parameters}, 'math': math}
        return eval(self.formula, {"__builtins__": {}}, safe_locals)

    def get_absolute_url(self):
        """URL to calculator detail (for interactive forms)."""
        return reverse('content:calculator-detail', kwargs={'slug': self.slug})
