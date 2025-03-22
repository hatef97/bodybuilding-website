from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch

from .models import Exercise, WorkoutPlan, WorkoutLog
from .serializers import ExerciseSerializer, WorkoutPlanSerializer, WorkoutLogSerializer, UserWorkoutLogSerializer



# Pagination settings
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100



class ExerciseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing exercises with optimized queryset and filtering.
    """
    serializer_class = ExerciseSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['name', 'category', 'id']
    search_fields = ['name', 'category']

    def get_permissions(self):
        """
        Override permissions for different actions.
        """
        if self.action == 'list':
            # Anyone can list exercises
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'destroy']:
            # Only admins can create, update, or delete exercises
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Override to optimize and filter queryset efficiently.
        """
        queryset = Exercise.objects.all()

        # Apply search filter (search across name and category)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(category__icontains=search_query))

        # Apply category filter
        category_filter = self.request.query_params.get('category', None)
        if category_filter:
            queryset = queryset.filter(category__icontains=category_filter)

        # Apply ordering if needed
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            queryset = queryset.order_by(ordering)

        # Apply select_related and prefetch_related for optimization
        queryset = queryset.select_related('workout_plan').prefetch_related('categories')

        return queryset



class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workout plans with optimized queries and flexible permissions.
    """
    serializer_class = WorkoutPlanSerializer
    pagination_class = StandardResultsSetPagination

    # Optimized queryset with prefetch_related to efficiently fetch exercises related to workout plans
    queryset = WorkoutPlan.objects.all().prefetch_related(
        Prefetch('exercises', queryset=Exercise.objects.all())  # Efficiently prefetch exercises
    )

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['name', 'created_at']
    search_fields = ['name']

    def get_permissions(self):
        """
        Override permissions for different actions.
        """
        if self.action == 'list':
            return [AllowAny()]  # Allow anyone to list workout plans
        elif self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or delete workout plans
        return [IsAuthenticated()]  # Default permission for all other actions

    def get_queryset(self):
        """
        Override to optimize and filter the queryset with additional filters and optimizations.
        """
        queryset = super().get_queryset()  # Start with the base queryset

        # Apply dynamic filters (search, category, etc.)
        queryset = self._apply_filters(queryset)

        # Return the optimized queryset with prefetching for exercises
        return queryset

    def _apply_filters(self, queryset):
        """
        Apply search, category, and ordering filters to the queryset dynamically.
        """
        search_query = self.request.query_params.get('search', None)
        category_filter = self.request.query_params.get('category', None)
        ordering = self.request.query_params.get('ordering', None)

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        if category_filter:
            queryset = queryset.filter(category__icontains=category_filter)

        if ordering:
            queryset = self._apply_ordering_filter(queryset, ordering)

        return queryset

    def _apply_ordering_filter(self, queryset, ordering):
        """
        Helper method to validate and apply ordering.
        """
        # Handle ordering by multiple fields, such as 'name,-created_at' for descending sorting
        ordering_fields = ordering.split(",") if ordering else ['name']
        queryset = queryset.order_by(*ordering_fields)
        return queryset

    @action(detail=True, methods=['get'])
    def exercises_in_plan(self, request, pk=None):
        """
        Custom action to retrieve all exercises for a given workout plan.
        Returns a list of exercises related to a specific workout plan.
        """
        workout_plan = self.get_object()  # Get the workout plan by ID (pk)
        exercises = workout_plan.exercises.all()  # Fetch related exercises
        serializer = ExerciseSerializer(exercises, many=True)  # Serialize exercises
        return Response(serializer.data)  # Return serialized exercises as response
        