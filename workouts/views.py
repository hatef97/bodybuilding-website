from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend

from .models import Exercise, WorkoutPlan, WorkoutLog
from .serializers import ExerciseSerializer, WorkoutPlanSerializer, WorkoutLogSerializer, UserWorkoutLogSerializer



# Pagination settings
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100
