from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from django.db.models import Q, Prefetch, Sum

from .models import *
from .serializers import *



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

    def handle_exception(self, exc):
        """
        Custom exception handling to ensure validation errors are returned with status 400.
        """
        if isinstance(exc, ValidationError):
            return Response({"detail": str(exc)}, status=400)
        return super().handle_exception(exc)



class MealPlanViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing MealPlan instances.
    """
    serializer_class = MealPlanSerializer
    pagination_class = StandardResultsSetPagination  # For pagination in large result sets

    def get_permissions(self):
        """
        Define the permissions for different actions.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or delete meal plans
        return [IsAuthenticated()]  # Any authenticated user can view or list meal plans

    def get_queryset(self):
        """
        Customize the queryset to allow filtering and searching for meal plans.
        """
        queryset = MealPlan.objects.all()

        # Search by meal plan name or description
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        # Filtering by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user__id=user_id)

        # Order by field
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            valid_ordering_fields = ['name', 'description', 'user']
            ordering_fields = ordering.split(',')

            for field in ordering_fields:
                if field.lstrip('-') not in valid_ordering_fields:
                    raise ValidationError(f"Invalid ordering field: {field}")

            queryset = queryset.order_by(*ordering_fields)

        return queryset

    def handle_exception(self, exc):
        """
        Override to handle validation errors and return them with a 400 status.
        """
        if isinstance(exc, ValidationError):
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return super().handle_exception(exc)

    def create(self, request, *args, **kwargs):
        """
        Handle creation of a MealPlan with related meals.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the meal plan with related meals
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Handle updating an existing MealPlan instance and its related meals.
        """
        meal_plan = self.get_object()
        serializer = self.get_serializer(meal_plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Update the meal plan with new meal data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Handle deleting a MealPlan instance.
        """
        meal_plan = self.get_object()
        meal_plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing recipes.
    """
    queryset = Recipe.objects.all().order_by('id')
    serializer_class = RecipeSerializer
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    def get_permissions(self):
        """
        Allow authenticated users to perform CRUD operations on meal plans.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or destroy meal plans
        return [IsAuthenticated()]  # Any authenticated user can list or view meal plans

    def update(self, request, *args, **kwargs):
        """
        Handle updating an existing Recipe instance.
        """
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Save the updated recipe
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalorieCalculatorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CalorieCalculator related operations.
    """
    serializer_class = CalorieCalculatorSerializer
    queryset = CalorieCalculator.objects.all()
    permission_classes = [IsAuthenticated]  # Only authenticated users can access
    pagination_class = StandardResultsSetPagination  # Use pagination for large result sets

    @action(detail=False, methods=['post'], url_path='calculate_calories')
    def calculate_calories(self, request):
        """
        Custom action to calculate the calories based on the provided data.
        The calculation will use a formula based on the provided data like age, weight, height, activity level, and gender.
        It will also save the provided data to the database.
        """
        serializer = CalorieCalculatorSerializer(data=request.data)

        if serializer.is_valid():
            # Perform the calorie calculation based on user data
            data = serializer.validated_data
            age = data['age']
            weight = data['weight']
            height = data['height']
            activity_level = data['activity_level']
            gender = data['gender']

            # Example Harris-Benedict Equation (BMR calculation)
            if gender == 'male':
                bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

            # Activity Level multiplier
            activity_multipliers = {
                'sedentary': 1.2,
                'light_activity': 1.375,
                'moderate_activity': 1.55,
                'heavy_activity': 1.725
            }

            calorie_need = bmr * activity_multipliers.get(activity_level, 1.2)

            # Save the calorie calculation result to the database
            calorie_calculator_instance = CalorieCalculator.objects.create(
                gender=gender,
                age=age,
                weight=weight,
                height=height,
                activity_level=activity_level
            )

            return Response({
                "calories_needed": calorie_need,
                "calorie_calculator_id": calorie_calculator_instance.id,
                "message": "Calorie calculation saved successfully"
            }, status=status.HTTP_200_OK)

        # If data is invalid, return a bad request with the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """
        Create a new CalorieCalculator instance (only for authenticated users).
        """
        return super().create(request, *args, **kwargs)
