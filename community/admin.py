from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from community.models import ForumPost, Comment, Challenge, Leaderboard, UserProfile



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



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for Comment.
    Allows quick moderation (activate/deactivate), filtering, and navigation.
    """
    list_display = (
        "id",
        "short_content",
        "author_link",
        "post_link",
        "created_at",
        "is_active",
    )
    list_display_links = ("id", "short_content")
    list_editable = ("is_active",)
    list_filter = ("is_active", "created_at", "user")
    search_fields = ("content", "user__username", "post__title")
    date_hierarchy = "created_at"
    raw_id_fields = ("user", "post")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("user", "post", "content", "is_active"),
        }),
        ("Meta", {
            "classes": ("collapse",),
            "fields": ("created_at",),
        }),
    )

    actions = ["make_active", "make_inactive"]

    def short_content(self, obj):
        """Truncate long comments for display."""
        text = obj.content
        return (text[:75] + "...") if len(text) > 75 else text
    short_content.short_description = "Comment"

    def author_link(self, obj):
        """Link to the comment’s author in the User admin."""
        url = reverse("admin:core_customuser_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    author_link.short_description = "Author"
    author_link.admin_order_field = "user__username"

    def post_link(self, obj):
        """Link to the related forum post in the admin."""
        url = reverse("admin:community_forumpost_change", args=[obj.post_id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = "Post"
    post_link.admin_order_field = "post__title"

    def make_active(self, request, queryset):
        """Admin action to mark selected comments as active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} comment(s) marked active.")
    make_active.short_description = "Mark selected comments Active"

    def make_inactive(self, request, queryset):
        """Admin action to mark selected comments as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} comment(s) marked inactive.")
    make_inactive.short_description = "Mark selected comments Inactive"



@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    """
    Admin configuration for Challenge.
    Enables quick filtering, search, participant management, and status toggles.
    """
    list_display = (
        "id",
        "name",
        "start_date",
        "end_date",
        "participant_count",
        "is_active",
    )
    list_display_links = ("id", "name")
    list_editable = ("is_active",)
    list_filter = (
        "is_active",
        "start_date",
        "end_date",
    )
    search_fields = ("name", "description")
    date_hierarchy = "start_date"
    readonly_fields = ("created_at",)
    ordering = ("-start_date",)
    filter_horizontal = ("participants",)

    fieldsets = (
        (None, {
            "fields": ("name", "description", "is_active")
        }),
        ("Schedule", {
            "classes": ("collapse",),
            "fields": ("start_date", "end_date", "created_at"),
        }),
        ("Participants", {
            "fields": ("participants",),
        }),
    )

    actions = ["make_active", "make_inactive"]

    def participant_count(self, obj):
        """Display number of participants, linked to filtered User list."""
        count = obj.participants.count()
        url = (
            reverse("admin:core_customuser_changelist")
            + f"?challenges__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">{} user(s)</a>', url, count)
    participant_count.short_description = "Participants"

    def make_active(self, request, queryset):
        """Admin action to mark selected challenges active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} challenge(s) marked active.")
    make_active.short_description = "Mark selected as Active"

    def make_inactive(self, request, queryset):
        """Admin action to mark selected challenges inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} challenge(s) marked inactive.")
    make_inactive.short_description = "Mark selected as Inactive"



@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """
    Admin configuration for Leaderboard.
    - Inline score editing
    - Quick filtering & search
    - Custom links to related Challenge and User
    - Batch actions to reset or adjust scores
    """
    list_display = (
        'id',
        'challenge_link',
        'user_link',
        'score',
    )
    list_display_links = ('id',)
    list_editable = ('score',)
    list_filter = ('challenge', 'user')
    search_fields = ('user__username', 'challenge__name')
    raw_id_fields = ('challenge', 'user')
    ordering = ('-score',)

    fieldsets = (
        (None, {
            'fields': ('challenge', 'user', 'score'),
        }),
    )

    actions = ['reset_scores', 'double_scores']

    def challenge_link(self, obj):
        """Link to the Challenge in the admin."""
        url = reverse('admin:community_challenge_change', args=[obj.challenge_id])
        return format_html('<a href="{}">{}</a>', url, obj.challenge.name)
    challenge_link.short_description = 'Challenge'
    challenge_link.admin_order_field = 'challenge__name'

    def user_link(self, obj):
        """Link to the User in the admin."""
        url = reverse('admin:core_customuser_change', args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'

    def reset_scores(self, request, queryset):
        """
        Batch action: Set selected scores to zero.
        """
        updated = queryset.update(score=0)
        self.message_user(request, f"{updated} score(s) reset to 0.")
    reset_scores.short_description = "Reset selected scores to zero"

    def double_scores(self, request, queryset):
        """
        Batch action: Double the score for selected entries.
        """
        for entry in queryset:
            entry.score = entry.score * 2
            entry.save()
        self.message_user(request, f"Doubled scores for {queryset.count()} entry(ies).")
    double_scores.short_description = "Double selected scores"



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin panel for UserProfile.
    - View and edit bio, social links, and picture.
    - Quick link to the related User.
    - Filters, search, and read-only timestamp.
    """
    list_display = (
        "id",
        "user_link",
        "short_bio",
        "created_at",
    )
    list_display_links = ("id", "user_link")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "bio")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("user", "bio", "profile_picture", "social_links"),
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at",),
        }),
    )

    def user_link(self, obj):
        """Clickable link to the User change page."""
        url = reverse("admin:core_customuser_change", args=[obj.user_id])
        return format_html("<a href='{}'>{}</a>", url, obj.user.username)
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"

    def short_bio(self, obj):
        """Truncate long bios for display."""
        if not obj.bio:
            return ""
        return (obj.bio[:75] + "...") if len(obj.bio) > 75 else obj.bio
    short_bio.short_description = "Bio"
    