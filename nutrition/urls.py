from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import MealViewSet, MealPlanViewSet, RecipeViewSet, CalorieCalculatorViewSet, MealInMealPlanViewSet



# Create a router instance to register viewsets
router = DefaultRouter()
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'mealplans', MealPlanViewSet, basename='mealplan')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'caloriecalculators', CalorieCalculatorViewSet, basename='caloriecalculator')
router.register(r'mealsinmealplan', MealInMealPlanViewSet, basename='mealinmealplan')

urlpatterns = [
    # Include the automatically generated URLs from the router
    path('', include(router.urls)),
]
