from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from community.models import ForumPost
from .serializers import ForumPostSerializer



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100



class ForumPostViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing, creating, updating, and deleting forum posts.
    """
    serializer_class = ForumPostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allows authenticated users to perform any action; others can only read.

    def perform_create(self, serializer):
        """
        Override perform_create to automatically set the 'user' field to the authenticated user.
        """
        user = self.request.user
        serializer.save(user=user)

    def get_queryset(self):
        """
        Optionally implement custom filtering or ordering here.
        This allows for more flexibility in retrieving the forum posts.
        """
        queryset = ForumPost.objects.all()

        # Get the 'is_active' query parameter
        is_active = self.request.query_params.get('is_active', None)

        if is_active is not None:
            # Handle valid 'true', 'false', '1', '0' values
            if is_active.lower() in ['true', '1']:
                is_active = True
            elif is_active.lower() in ['false', '0']:
                is_active = False
            else:
                # If it's an invalid value, raise a ValidationError
                raise ValidationError("is_active must be a valid boolean (1 or 0, or 'true'/'false').")
            
            # If valid, filter the posts by 'is_active' value
            queryset = queryset.filter(is_active=is_active)

        return queryset

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        A custom action to toggle the 'is_active' status of a forum post.
        """
        post = self.get_object()
        post.is_active = not post.is_active
        post.save()

        return Response({
            'status': 'success',
            'is_active': post.is_active
        }, status=status.HTTP_200_OK)
