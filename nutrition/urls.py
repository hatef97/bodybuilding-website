from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import *



# Create a router instance to register viewsets
router = DefaultRouter()
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'mealplans', MealPlanViewSet, basename='mealplan')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'caloriecalculators', CalorieCalculatorViewSet, basename='caloriecalculator')

urlpatterns = [
    path('', include(router.urls)),
    # Manually define the URL pattern for the custom action
    path('caloriecalculators/calculate_calories/', CalorieCalculatorViewSet.as_view({'post': 'calculate_calories'}), name='caloriecalculator-calculate_calories'),
]
