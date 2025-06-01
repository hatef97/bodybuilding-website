import math
from datetime import timedelta

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from .models import Article, Video, ExerciseGuide, FitnessMeasurement
from core.models import CustomUser as User



@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Article model:
    • Draft/publish workflow
    • Auto-slug management
    • Featured image preview
    • Bulk publish/draft actions
    """

    # Columns to show in list view
    list_display = (
        'id', 'title', 'author_link', 'status', 'is_published', 'published_at',
    )
    list_display_links = ('id', 'title')
    list_editable = ('is_published',)
    list_filter = ('status', 'is_published', 'author', 'published_at')
    search_fields = ('title', 'excerpt', 'content', 'author__username')
    date_hierarchy = 'published_at'

    # Prepopulate slug from title, raw lookup for author FK
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)

    # Read-only fields and custom preview
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')

    # Organize fields into collapsible sections
    fieldsets = (
        (None, {
            'fields': (
                'title', 'slug', 'author', 'excerpt', 'content', 'featured_image',
            )
        }),
        ('Publication', {
            'classes': ('collapse',),
            'fields': (
                'status', 'is_published', 'published_at', 'thumbnail_preview',
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    # Custom bulk actions
    actions = ['make_published', 'make_draft']

    def author_link(self, obj):
        """
        Render the author as a clickable link to their user-change page.
        """
        if obj.author_id:
            url = reverse('admin:core_customuser_change', args=[obj.author_id])
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return '-'
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__username'

    def thumbnail_preview(self, obj):
        """
        Show a small preview of the featured image.
        """
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height:150px; max-width:200px; object-fit:contain;" />',
                obj.featured_image.url
            )
        return '(No image)'
    thumbnail_preview.short_description = 'Featured Image'

    def make_published(self, request, queryset):
        """
        Bulk action: mark selected articles as published now.
        """
        updated = queryset.update(
            status=Article.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} article(s) marked as Published")
    make_published.short_description = "Mark selected as Published"

    def make_draft(self, request, queryset):
        """
        Bulk action: revert selected articles back to draft.
        """
        updated = queryset.update(
            status=Article.STATUS_DRAFT,
            is_published=False
        )
        self.message_user(request, f"{updated} article(s) reverted to Draft")
    make_draft.short_description = "Revert selected to Draft"



@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Video model:
      • Manage draft/publish workflow
      • Auto-slug management
      • Thumbnail preview
      • Bulk publish/draft actions
    """

    # Columns shown in the list view
    list_display = (
        'id', 'title', 'author_link', 'status', 'is_published',
        'published_at', 'duration_display',
    )
    list_display_links = ('id', 'title')
    list_editable = ('is_published',)
    list_filter = ('status', 'is_published', 'author', 'published_at')
    search_fields = ('title', 'description', 'author__username')
    date_hierarchy = 'published_at'

    # Prepopulate slug from title and raw-id lookup for author
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)

    # Read-only fields and previews
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')

    # Organize fields into logical sections
    fieldsets = (
        (None, {
            'fields': (
                'title', 'slug', 'url', 'embed_code',
                'description', 'thumbnail',
            )
        }),
        ('Publication', {
            'classes': ('collapse',),
            'fields': (
                'status', 'is_published', 'published_at',
                'thumbnail_preview',
            )
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('duration', 'author'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    # Bulk actions
    actions = ['make_published', 'make_draft']

    def author_link(self, obj):
        """Clickable link to the author in the User admin."""
        if obj.author_id:
            url = reverse('admin:core_customuser_change', args=[obj.author_id])
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return '-'
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__username'

    def thumbnail_preview(self, obj):
        """Render a small preview of the video thumbnail."""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height:120px; max-width:160px; object-fit:cover;" />',
                obj.thumbnail.url
            )
        return '(No thumbnail)'
    thumbnail_preview.short_description = 'Thumbnail'

    def duration_display(self, obj):
        """Format duration as H:MM:SS or blank."""
        return str(obj.duration) if obj.duration else '-'
    duration_display.short_description = 'Duration'

    def make_published(self, request, queryset):
        """Bulk action: mark selected videos as published now."""
        updated = queryset.update(
            status=Video.STATUS_PUBLISHED,
            is_published=True,
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} video(s) marked as published.")
    make_published.short_description = "Mark selected as Published"

    def make_draft(self, request, queryset):
        """Bulk action: revert selected videos to draft."""
        updated = queryset.update(
            status=Video.STATUS_DRAFT,
            is_published=False
        )
        self.message_user(request, f"{updated} video(s) reverted to draft.")
    make_draft.short_description = "Revert selected to Draft"



@admin.register(ExerciseGuide)
class ExerciseGuideAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for the ExerciseGuide model.
    """
    # Columns displayed in list view
    list_display = (
        'name',
        'slug',
        'difficulty',
        'primary_muscle',
        'equipment_required',
        'author',
        'created_at',
        'updated_at',
    )

    # Make slug read-only (auto-generated)
    readonly_fields = ('slug', 'created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        """
        Make 'slug' writable on add forms; read-only on change forms.
        """
        # On add (obj is None), exclude slug from readonly_fields
        if obj is None:
            return [f for f in self.readonly_fields if f != 'slug']
        return self.readonly_fields

    # Fields automatically populated from other fields
    prepopulated_fields = {
        'slug': ('name',),
    }

    # Filters in the sidebar
    list_filter = (
        'difficulty',
        'primary_muscle',
        'author',
    )

    # Searchable fields
    search_fields = (
        'name',
        'excerpt',
        'steps',
        'equipment_required',
    )

    # Default ordering
    ordering = ('name',)

    # Organize fields into collapsible sections
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'author')
        }),
        ('Content', {
            'fields': ('excerpt', 'steps')
        }),
        ('Attributes', {
            'fields': ('difficulty', 'primary_muscle', 'equipment_required')
        }),
        ('Media', {
            'fields': ('image', 'video_embed')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )



@admin.register(FitnessMeasurement)
class FitnessMeasurementAdmin(admin.ModelAdmin):
    """
    Admin interface for FitnessMeasurement:
    - list_display shows user, height, weight, BMI, BSA, category, date_of_birth, gender, created/updated.
    - list_filter for user, gender, and date_of_birth.
    - search_fields to find by user username/email.
    - readonly_fields for computed properties and timestamps.
    - fieldsets to group core vs. computed vs. metadata.
    """

    # Columns displayed in the changelist
    list_display = (
        "id",
        "user_link",
        "height_cm",
        "weight_kg",
        "height_m_display",
        "bmi_display",
        "bmi_category_display",
        "bsa_display",
        "gender",
        "date_of_birth",
        "created_at",
        "updated_at",
    )

    # Filters in the right sidebar
    list_filter = (
        "gender",
        "date_of_birth",
        "user__username",
    )

    # Searchable by user’s username or email
    search_fields = (
        "user__username",
        "user__email",
    )

    # Fields that should be read-only in the detail/edit form
    readonly_fields = (
        "height_m_display",
        "bmi_display",
        "bmi_category_display",
        "bsa_display",
        "created_at",
        "updated_at",
    )

    # Group fields into fieldsets for clarity
    fieldsets = (
        (
            "Core Measurement Data",
            {
                "fields": (
                    "user",
                    ("height_cm", "weight_kg"),
                    "gender",
                    "date_of_birth",
                )
            },
        ),
        (
            "Computed Properties (Read‐Only)",
            {
                "fields": (
                    "height_m_display",
                    "bmi_display",
                    "bmi_category_display",
                    "bsa_display",
                ),
                "description": "These values are auto‐computed from height_cm and weight_kg.",
            },
        ),
        (
            "Timestamps (Read‐Only)",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    ordering = ("-created_at",)

    def get_queryset(self, request):
        """
        Override to prefetch related user to avoid an extra query per row in list_display.
        """
        qs = super().get_queryset(request)
        return qs.select_related("user")

    def user_link(self, obj):
        """
        Show a clickable link to the related User’s admin change page.
        """
        if obj.user:
            url = reverse(
                "admin:%s_%s_change"
                % (User._meta.app_label, User._meta.model_name),
                args=[obj.user.pk],
            )
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "-"
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"

    def height_m_display(self, obj):
        """
        Display height in meters (read‐only). Guard against None.
        """
        if obj.height_cm is None:
            return "-"
        # Convert to meters and format two decimal places
        height_m = obj.height_cm / 100.0
        return f"{height_m:.2f} m"
    height_m_display.short_description = "Height (m)"
    height_m_display.admin_order_field = "height_cm"

    def bmi_display(self, obj):
        """
        Display BMI = weight_kg / (height_m^2), rounded to two decimals.
        Guard against missing height or weight.
        """
        if obj.height_cm is None or obj.weight_kg is None:
            return "-"
        height_m = obj.height_cm / 100.0
        if height_m <= 0:
            return "0.00"
        bmi_val = obj.weight_kg / (height_m * height_m)
        return f"{bmi_val:.2f}"
    bmi_display.short_description = "BMI"
    # Order by weight_kg roughly approximates BMI sorting
    bmi_display.admin_order_field = "weight_kg"

    def bmi_category_display(self, obj):
        """
        Display BMI category (Underweight, Normal, Overweight, Obese).
        Guard against missing height or weight.
        """
        if obj.height_cm is None or obj.weight_kg is None:
            return "-"
        height_m = obj.height_cm / 100.0
        if height_m <= 0:
            return "-"
        bmi_val = obj.weight_kg / (height_m * height_m)
        if bmi_val < 18.5:
            return "Underweight"
        if bmi_val < 25:
            return "Normal weight"
        if bmi_val < 30:
            return "Overweight"
        return "Obese"
    bmi_category_display.short_description = "BMI Category"
    bmi_category_display.admin_order_field = "weight_kg"

    def bsa_display(self, obj):
        """
        Display BSA (Mosteller) = sqrt((height_cm * weight_kg) / 3600), rounded to two decimals.
        Guard against missing height or weight.
        """
        if obj.height_cm is None or obj.weight_kg is None:
            return "-"
        # If either is zero, formula yields 0.0
        if obj.height_cm <= 0 or obj.weight_kg <= 0:
            return "0.00 m²"
        bsa_val = math.sqrt((obj.height_cm * obj.weight_kg) / 3600.0)
        return f"{bsa_val:.2f} m²"
    bsa_display.short_description = "BSA"
    bsa_display.admin_order_field = "height_cm"
