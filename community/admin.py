from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from community.models import ForumPost



@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    """Admin panel configuration for ForumPost."""

    # Columns to display in the list view
    list_display = (
        'id',
        'title',
        'author_link',
        'created_at',
        'updated_at',
        'is_active',
    )
    list_display_links = ('id', 'title')
    
    # Fields you can click through to edit
    list_editable = ('is_active',)
    
    # Enable filtering by these fields
    list_filter = (
        'is_active',
        'created_at',
        'updated_at',
        'user',
    )
    
    # Add a date hierarchy navigation by creation date
    date_hierarchy = 'created_at'
    
    # Make the created/updated fields read-only in the detail view
    readonly_fields = ('created_at', 'updated_at')
    
    # Which fields to search across
    search_fields = ('title', 'content', 'user__username', 'user__email')
    
    # Optimize foreign-key lookups
    raw_id_fields = ('user',)
    
    # Default ordering
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'content', 'is_active')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    actions = ['make_active', 'make_inactive']

    def author_link(self, obj):
        """Link to the related user in the auth.User admin."""
        url = (
            reverse('admin:core_customuser_change', args=(obj.user_id,))
            if obj.user_id else ''
        )
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'user__username'

    def make_active(self, request, queryset):
        """Admin action to mark selected posts active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} post(s) marked as active.")
    make_active.short_description = "Mark selected posts as Active"

    def make_inactive(self, request, queryset):
        """Admin action to mark selected posts inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} post(s) marked as inactive.")
    make_inactive.short_description = "Mark selected posts as Inactive"
