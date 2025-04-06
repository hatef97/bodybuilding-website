from django.contrib import admin

from .models import CalorieCalculator, Meal, Recipe, MealPlan



# CalorieCalculator Admin
class CalorieCalculatorAdmin(admin.ModelAdmin):
    list_display = ('gender', 'age', 'weight', 'height', 'activity_level', 'calculated_calories')
    search_fields = ('gender', 'age', 'weight', 'height')
    list_filter = ('gender', 'activity_level')
    readonly_fields = ('calculated_calories',)

    def calculated_calories(self, obj):
        """Method to display the calculated calories in list_display."""
        return obj.calculate_calories()
    calculated_calories.short_description = 'Calculated Calories'

    def save_model(self, request, obj, form, change):
        """Custom save method to automatically set the user"""
        obj.save()

admin.site.register(CalorieCalculator, CalorieCalculatorAdmin)



# Meal Admin
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat')
    search_fields = ('name',)
    list_filter = ('calories',)
    ordering = ('name',)

    def save_model(self, request, obj, form, change):
        obj.save()

admin.site.register(Meal, MealAdmin)



# Recipe Admin
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('meal', 'instructions_preview', 'ingredients_preview')
    search_fields = ('meal__name', 'instructions', 'ingredients')
    ordering = ('meal__name',)

    def instructions_preview(self, obj):
        """Displays a preview of the instructions."""
        return obj.instructions[:50] + "..." if len(obj.instructions) > 50 else obj.instructions

    def ingredients_preview(self, obj):
        """Displays a preview of the ingredients."""
        return obj.ingredients[:50] + "..." if len(obj.ingredients) > 50 else obj.ingredients

    instructions_preview.short_description = 'Instructions Preview'
    ingredients_preview.short_description = 'Ingredients Preview'

admin.site.register(Recipe, RecipeAdmin)



# MealPlan Admin
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'meal_count')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

    def meal_count(self, obj):
        """Displays the number of meals in the meal plan."""
        return obj.meals.count()

    meal_count.short_description = 'Meal Count'

admin.site.register(MealPlan, MealPlanAdmin)
