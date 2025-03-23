from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch, Sum
from django.utils import timezone

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
        queryset = queryset.prefetch_related('workout_plans')

        return queryset



class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workout plans with optimized queries and flexible permissions.
    """
    serializer_class = WorkoutPlanSerializer
    pagination_class = StandardResultsSetPagination
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
        queryset = WorkoutPlan.objects.all()  # Start with the base queryset

        # Apply dynamic filters (search, category, etc.)
        queryset = self._apply_filters(queryset)

        # Apply prefetch_related for related objects to minimize the number of queries
        queryset = queryset.prefetch_related('exercises')  # Example: Pre-fetch exercises if needed

        return queryset

    def _apply_filters(self, queryset):
        """
        Apply search, category, and ordering filters to the queryset dynamically.
        """
        search_query = self.request.query_params.get('search', None)
        category_filter = self.request.query_params.get('category', None)
        ordering = self.request.query_params.get('ordering', None)

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(category__icontains=search_query)
            )

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
        valid_fields = ['name', 'created_at', 'category']  # Add more valid fields here
        ordering_fields = ordering.split(",") if ordering else ['name']

        # Validate ordering fields
        ordering_fields = [field for field in ordering_fields if field.lstrip('-') in valid_fields]

        # Apply the valid ordering fields
        if ordering_fields:
            queryset = queryset.order_by(*ordering_fields)
        else:
            queryset = queryset.order_by('name')  # Default ordering by 'name'

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



class WorkoutLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking individual workout logs with optimized queries and flexible permissions.
    """
    serializer_class = WorkoutLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['date', 'duration']
    search_fields = ['workout_plan__name', 'user__email']

    def get_permissions(self):
        """
        Override permissions for different actions.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create, update, or delete workout plans
        return [IsAuthenticated()]  # Default permission for all other actions

    def get_queryset(self):
        """
        Override to optimize and filter the queryset with additional filters and optimizations.
        """
        # Start with the base queryset and apply prefetch for related data.
        queryset = WorkoutLog.objects.all().select_related('user', 'workout_plan').prefetch_related(
            'exercises'  # Efficiently prefetch exercises related to workout logs
        )

        # Apply dynamic filters (search, category, etc.)
        queryset = self._apply_filters(queryset)

        # Return the optimized queryset
        return queryset

    def perform_create(self, serializer):
        """
        Override the create method to automatically associate the log with the current user.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def user_logs(self, request, pk=None):
        """
        Custom action to view logs of the currently authenticated user.
        """
        user = self.request.user
        workout_logs = WorkoutLog.objects.filter(user=user)
        serializer = UserWorkoutLogSerializer(workout_logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today_logs(self, request):
        """
        Custom action to retrieve today's workout logs for the authenticated user.
        """
        today = timezone.now().date()
        workout_logs = WorkoutLog.objects.filter(user=request.user, date=today)
        serializer = UserWorkoutLogSerializer(workout_logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_workout_summary(self, request):
        """
        Custom action to provide a summary of the user's workout progress.
        """
        user = request.user
        workout_logs = WorkoutLog.objects.filter(user=user)

        total_workouts = workout_logs.count()
        total_duration = workout_logs.aggregate(Sum('duration'))['duration__sum'] or 0

        summary = {
            'total_workouts': total_workouts,
            'total_duration': total_duration,
        }

        return Response(summary, status=status.HTTP_200_OK)
