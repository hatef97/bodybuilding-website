from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Article



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
