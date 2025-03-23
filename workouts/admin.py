from django.contrib import admin

from .models import Exercise, WorkoutPlan



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



# Register the Exercise model with the custom ExerciseAdmin
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
