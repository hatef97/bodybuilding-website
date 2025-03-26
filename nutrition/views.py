from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from django.db.models import Q, Prefetch, Sum

from .models import Meal, MealPlan, Recipe, CalorieCalculator, MealInMealPlan
from .serializers import MealSerializer, MealPlanSerializer, RecipeSerializer, CalorieCalculatorSerializer, MealInMealPlanSerializer



# Custom Pagination Class for Search Results
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Set the default page size for pagination
    page_size_query_param = 'page_size'
    max_page_size = 100  # Limit the maximum page size



class MealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing meals.
    """
    serializer_class = MealSerializer
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    def get_permissions(self):
        """
        Allow authenticated users to perform CRUD operations on meals.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or destroy meals
        return [IsAuthenticated()]  # Any authenticated user can list or view meals

    def get_queryset(self):
        """
        Customize the queryset for search, category filters, etc.
        """
        queryset = Meal.objects.all()

        # Apply search filter (by name or description)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Apply ordering and validate ordering fields
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            valid_ordering_fields = ['name', 'calories']  # Example: list of valid fields
            ordering_fields = ordering.split(',')

            # Validate ordering fields
            for field in ordering_fields:
                if field.lstrip('-') not in valid_ordering_fields:
                    raise ValidationError(f"Invalid ordering field: {field}")

            queryset = queryset.order_by(*ordering_fields)

        return queryset



class MealPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing meal plans with optimized queries and flexible permissions.
    """
    serializer_class = MealPlanSerializer
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    def get_permissions(self):
        """
        Allow authenticated users to perform CRUD operations on meal plans.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or destroy meal plans
        return [IsAuthenticated()]  # Any authenticated user can list or view meal plans

    def get_queryset(self):
        """
        Override to optimize and filter the queryset with additional filters and optimizations.
        """
        queryset = MealPlan.objects.all()

        # Prefetch related meals to optimize queries when retrieving meal plans
        queryset = queryset.prefetch_related(
            Prefetch('meals', queryset=Meal.objects.all())  # Prefetch the meals related to meal plans
        )

        # Apply custom filters (e.g., by goal, name, etc.)
        goal = self.request.query_params.get('goal', None)
        if goal:
            queryset = queryset.filter(goal=goal)

        # Optional: Annotate with total calories, protein, etc.
        queryset = queryset.annotate(
            total_calories=Sum('meals__calories'),
            total_protein=Sum('meals__protein'),
            total_carbs=Sum('meals__carbs'),
            total_fats=Sum('meals__fats')
        )

        return queryset

    @action(detail=True, methods=['get'])
    def meal_summary(self, request, pk=None):
        """
        Custom action to get the summary of total nutrients for a given meal plan.
        """
        meal_plan = self.get_object()

        # Prepare summary data
        summary_data = {
            'total_calories': meal_plan.total_calories,
            'total_protein': meal_plan.total_protein,
            'total_carbs': meal_plan.total_carbs,
            'total_fats': meal_plan.total_fats,
        }

        # Serialize the summary data
        serializer = MealPlanSummarySerializer(data=summary_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)



class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing recipes.
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    def get_permissions(self):
        """
        Allow authenticated users to perform CRUD operations on meal plans.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or destroy meal plans
        return [IsAuthenticated()]  # Any authenticated user can list or view meal plans
