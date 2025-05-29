from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Article, Video, ExerciseGuide



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
