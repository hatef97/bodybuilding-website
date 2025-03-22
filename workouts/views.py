from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

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
