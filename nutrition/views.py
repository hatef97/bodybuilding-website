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



class CalorieCalculatorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for calculating daily calorie requirements based on user input.
    """
    queryset = CalorieCalculator.objects.all()
    serializer_class = CalorieCalculatorSerializer
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    def get_permissions(self):
        """
        Allow authenticated users to perform CRUD operations on meal plans.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or destroy meal plans
        return [IsAuthenticated()]  # Any authenticated user can list or view meal plans


    @action(detail=False, methods=['get'])
    def calculate(self, request):
        """
        Custom action to calculate daily calories based on user input.
        """
        age = request.query_params.get('age')
        weight = request.query_params.get('weight')
        height = request.query_params.get('height')
        activity_level = request.query_params.get('activity_level')
        goal = request.query_params.get('goal')
        gender = request.query_params.get('gender')

        if not all([age, weight, height, activity_level, goal, gender]):
            return Response({"detail": "All parameters must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        calorie_calculator = CalorieCalculator(
            age=int(age),
            weight=float(weight),
            height=float(height),
            activity_level=activity_level,
            goal=goal,
            gender=gender
        )

        calories = calorie_calculator.calculate_calories()

        return Response({"daily_calories": calories}, status=status.HTTP_200_OK)



# Create a MealInMealPlanViewSet for handling the many-to-many relation between Meal and MealPlan.
class MealInMealPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for adding meals to a meal plan.
    """
    serializer_class = MealInMealPlanSerializer
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
        Customize the queryset to filter by the meal plan and user.
        """
        queryset = MealInMealPlan.objects.all()

        # Ensure you're passing the MealPlan instance or its ID
        meal_plan_id = self.request.query_params.get('meal_plan', None)
        if meal_plan_id:
            try:
                # Ensure you're querying by ID, not email or other parameters
                meal_plan = MealPlan.objects.get(id=meal_plan_id)
                queryset = queryset.filter(meal_plan=meal_plan)
            except MealPlan.DoesNotExist:
                # Handle error if MealPlan is not found
                raise ValidationError("MealPlan with the provided ID does not exist.")

        # # Optionally, you can add a filter to allow access to only the authenticated user's meal plans
        # if self.request.user.is_authenticated:
        #     queryset = queryset.filter(meal_plan__user=self.request.user)

        # Prefetch related meals to optimize queries when retrieving meal plans
        queryset = queryset.prefetch_related(
            Prefetch('meal', queryset=Meal.objects.all())  # Prefetch meals
        )

        return queryset

    @action(detail=True, methods=['get'])
    def meal_plan(self, request, pk=None):
        """
        Custom action to retrieve all meals in a specific meal plan.
        """
        meal_in_meal_plan = self.get_object()
        meal_plan = meal_in_meal_plan.meal_plan
        meals = meal_plan.meals.all()
        serializer = MealSerializer(meals, many=True)
        return Response(serializer.data)
