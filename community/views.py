from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from community.models import ForumPost
from .serializers import ForumPostSerializer



class ForumPostViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing, creating, updating, and deleting forum posts.
    """
    serializer_class = ForumPostSerializer
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

        # Example of filtering by whether the post is active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            # Ensure is_active is a valid boolean
            try:
                is_active = bool(int(is_active))  # Convert to boolean
                queryset = queryset.filter(is_active=is_active)
            except ValueError:
                raise serializers.ValidationError("is_active must be a valid boolean (1 or 0).")

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
