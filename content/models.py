from django.conf import settings
from django.db import models
from django.urls import reverse
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

    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(
        max_length=255,
        unique=True,
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
    objects = models.Manager()        # The default manager.
    published = PublishedManager()    # Returns only is_published=True.

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
        # Ensure published_at is set if published
        if self.is_published and not self.published_at:
            raise models.ValidationError("published_at must be set when is_published=True.")

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base
            n = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # If setting to published but no timestamp, set it now
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the public URL for this article."""
        return reverse('content:article-detail', kwargs={'slug': self.slug})



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
            raise models.ValidationError("published_at must be set when is_published=True.")
        # Must have either URL or embed_code
        if not (self.url or self.embed_code):
            raise models.ValidationError("Provide either a URL or embed code for the video.")

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
        return reverse('content:video-detail', kwargs={'slug': self.slug})
