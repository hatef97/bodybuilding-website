from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Fields displayed in the list view
    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth', 
        'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions')

    # Fieldsets for the edit form (view and update)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name', 'date_of_birth', 'username')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields displayed when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'first_name', 'last_name', 
                       'date_of_birth', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    # Actions for admin (optional: you can add custom actions for bulk actions in the admin panel)
    actions = ['make_active', 'make_inactive']


    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected users have been activated.")


    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected users have been deactivated.")

    make_active.short_description = "Activate selected users"
    make_inactive.short_description = "Deactivate selected users"



admin.site.register(CustomUser, CustomUserAdmin)
