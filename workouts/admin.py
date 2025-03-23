from django.contrib import admin
from django.contrib.auth.models import User

from .models import Exercise, WorkoutPlan, WorkoutLog



class ExerciseAdmin(admin.ModelAdmin):
    """
    Admin panel for managing exercises.
    """
    # Fields to display in the admin panel list view
    list_display = ('name', 'category', 'description', 'video_url', 'get_category_display')

    # Fields to filter by in the admin panel
    list_filter = ('category',)

    # Fields to enable searching by name or category
    search_fields = ('name', 'category')

    # Define the fields that should be editable directly in the list view
    list_editable = ('category',)  # Example: Allow the category to be edited directly in the list view

    # Enable pagination in the list view
    list_per_page = 20  # Show 20 exercises per page in the admin

    # Allow ordering by name or category
    ordering = ('name',)  # Default ordering by name

    # Define a custom action to change the category of selected exercises
    actions = ['set_strength_category', 'set_cardio_category']

    def set_strength_category(self, request, queryset):
        """
        Custom admin action to set the category to 'Strength' for selected exercises.
        """
        rows_updated = queryset.update(category='Strength')
        self.message_user(request, f"{rows_updated} exercises were successfully updated to Strength category.")
    set_strength_category.short_description = "Set selected exercises to Strength category"

    def set_cardio_category(self, request, queryset):
        """
        Custom admin action to set the category to 'Cardio' for selected exercises.
        """
        rows_updated = queryset.update(category='Cardio')
        self.message_user(request, f"{rows_updated} exercises were successfully updated to Cardio category.")
    set_cardio_category.short_description = "Set selected exercises to Cardio category"

    # Customize how the category is displayed
    def get_category_display(self, obj):
        """
        This method allows the category to be displayed by its human-readable name.
        """
        return obj.get_category_display()  # This will show the human-readable value of the 'category' field
    get_category_display.short_description = 'Category'  # Label for the column in the admin



class WorkoutPlanAdmin(admin.ModelAdmin):
    """
    Admin panel for managing workout plans.
    """
    # Fields to display in the list view
    list_display = ('name', 'created_at', 'updated_at', 'exercise_count', 'short_description')
    
    # Fields to filter by in the list view
    list_filter = ('created_at', 'updated_at')
    
    # Fields to search by in the list view
    search_fields = ('name', 'description')
    
    # Enable pagination
    list_per_page = 20
    
    # Enable ordering by name or created_at
    ordering = ('created_at',)
    
    # Enable date hierarchy for easy navigation by created date
    date_hierarchy = 'created_at'
    
    # Show exercises in a horizontal filter (Many-to-Many relationship)
    filter_horizontal = ('exercises',)
    
    # Custom action to get the number of exercises in each plan
    def exercise_count(self, obj):
        """
        Custom method to get the count of exercises in a workout plan.
        """
        return obj.exercises.count()
    exercise_count.short_description = 'Number of Exercises'  # Column name in the admin
    
    # Custom method to shorten description
    def short_description(self, obj):
        """
        Custom method to display a shortened version of the description in the list view.
        """
        return (obj.description[:50] + '...') if obj.description else 'No description'
    short_description.short_description = 'Description'



class WorkoutLogAdmin(admin.ModelAdmin):
    """
    Admin panel for managing individual workout logs.
    """
    # Fields to display in the list view
    list_display = ('user_email', 'workout_plan_name', 'date', 'duration_in_minutes', 'notes_snippet', 'formatted_date')

    # Fields to filter by in the list view
    list_filter = ('user', 'workout_plan', 'date')

    # Fields to search by in the list view
    search_fields = ('user__email', 'workout_plan__name')

    # Number of records per page
    list_per_page = 20

    # Default ordering for the admin list view
    ordering = ('-date',)  # Order by date in descending order

    # Display the user email in the list display
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    # Display the workout plan name in the list display
    def workout_plan_name(self, obj):
        return obj.workout_plan.name
    workout_plan_name.short_description = 'Workout Plan Name'

    # Display duration in minutes as a nice readable string
    def duration_in_minutes(self, obj):
        return f'{obj.duration} minutes'
    duration_in_minutes.short_description = 'Duration'

    # Show a truncated version of the notes for quick preview
    def notes_snippet(self, obj):
        return obj.notes[:50] + '...' if obj.notes else 'No notes'
    notes_snippet.short_description = 'Notes'

    # Display the date in a more readable format
    def formatted_date(self, obj):
        return obj.date.strftime('%b %d, %Y')  # Display date in a readable format like "Sep 18, 2022"
    formatted_date.short_description = 'Workout Date'

    # Allow date-based hierarchy for better navigation
    date_hierarchy = 'date'

    # Inlines for workout plan and user details (optional, could be useful if the WorkoutLog is related to these)
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)



# Register the Exercise model with the custom ExerciseAdmin
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
