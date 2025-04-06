from django.contrib import admin
from django.utils.html import format_html

from .models import WeightLog, BodyMeasurement, ProgressLog



# Custom Admin for WeightLog
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight_kg', 'date_logged', 'view_user')
    list_filter = ('date_logged', 'user')
    search_fields = ('user__username', 'weight_kg')
    date_hierarchy = 'date_logged'
    ordering = ('-date_logged',)

    # Optional: Add custom methods to format data
    def view_user(self, obj):
        return format_html('<b>{}</b>', obj.user.username)
    view_user.short_description = 'User'

    # Add actions for mass update
    actions = ['reset_weights']

    def reset_weights(self, request, queryset):
        queryset.update(weight_kg=0)
        self.message_user(request, "Weights reset successfully.")
    reset_weights.short_description = "Reset selected weights to 0"



# Custom Admin for BodyMeasurement
class BodyMeasurementAdmin(admin.ModelAdmin):
    list_display = ('user', 'chest_cm', 'waist_cm', 'hips_cm', 'date_logged', 'view_user')
    list_filter = ('date_logged', 'user')
    search_fields = ('user__username',)
    date_hierarchy = 'date_logged'
    ordering = ('-date_logged',)

    def view_user(self, obj):
        return format_html('<b>{}</b>', obj.user.username)
    view_user.short_description = 'User'



# Custom Admin for ProgressLog
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'date_logged', 'note', 'view_user')
    list_filter = ('date_logged', 'user')
    search_fields = ('user__username', 'title', 'note')
    date_hierarchy = 'date_logged'
    ordering = ('-date_logged',)

    def view_user(self, obj):
        return format_html('<b>{}</b>', obj.user.username)
    view_user.short_description = 'User'

    # Optional: Show image thumbnail in the admin panel
    def get_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50"/>'.format(obj.image.url))
        return "No image"
    get_image.short_description = 'Image'



# Register models with custom admin
admin.site.register(WeightLog, WeightLogAdmin)
admin.site.register(BodyMeasurement, BodyMeasurementAdmin)
admin.site.register(ProgressLog, ProgressLogAdmin)
