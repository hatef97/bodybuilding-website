from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from django.db.models import Q

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
                Q(description__icontains=search_query) |
                Q(category__icontains=search_query)
            )

        # Apply category filter
        category_filter = self.request.query_params.get('category', None)
        if category_filter:
            queryset = queryset.filter(category__icontains=category_filter)

        # Apply ordering and validate ordering fields
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            valid_ordering_fields = ['name', 'category', 'calories']  # Example: list of valid fields
            ordering_fields = ordering.split(',')

            # Validate ordering fields
            for field in ordering_fields:
                if field.lstrip('-') not in valid_ordering_fields:
                    raise ValidationError(f"Invalid ordering field: {field}")

            queryset = queryset.order_by(*ordering_fields)

        return queryset
