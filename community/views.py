from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from community.models import ForumPost, Comment
from .serializers import ForumPostSerializer, CommentSerializer



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



class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Comment objects on forum posts.
    Supports CRUD operations and a custom action to soft-delete (deactivate) comments.
    """
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optionally filters comments by `post` and `is_active`.
        """
        queryset = Comment.objects.all()
        post_id = self.request.query_params.get('post')
        is_active = self.request.query_params.get('is_active')

        if post_id is not None:
            queryset = queryset.filter(post_id=post_id)

        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
            else:
                raise ValidationError("`is_active` must be a valid boolean value: true/false or 1/0.")

        return queryset

    def perform_create(self, serializer):
        """
        Automatically assign the authenticated user as the comment author.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """
        Custom action to toggle a comment's active status (soft delete or restore).
        """
        comment = self.get_object()
        comment.is_active = not comment.is_active
        comment.save()
        return Response(
            {
                'status': 'success',
                'is_active': comment.is_active
            },
            status=status.HTTP_200_OK
        )
