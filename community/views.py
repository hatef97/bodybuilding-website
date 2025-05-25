from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from community.models import ForumPost, Comment, Challenge, Leaderboard, UserProfile
from .serializers import ForumPostSerializer, CommentSerializer, ChallengeSerializer, LeaderboardSerializer, UserProfileSerializer



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



class ChallengeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Challenges where users can compete.
    Includes full CRUD operations and custom join/leave actions.
    """
    serializer_class = ChallengeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optionally filter challenges by:
        - is_active=true/false
        - upcoming (start_date > now)
        - past (end_date < now)
        """
        queryset = Challenge.objects.all()
        params = self.request.query_params

        is_active = params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
            else:
                raise ValidationError("`is_active` must be true/false or 1/0.")

        filter_type = params.get('filter')
        if filter_type == 'upcoming':
            queryset = queryset.filter(start_date__gt=timezone.now())
        elif filter_type == 'past':
            queryset = queryset.filter(end_date__lt=timezone.now())

        return queryset

    def perform_create(self, serializer):
        """
        Optionally add the current user to the participants if not provided.
        """
        challenge = serializer.save()
        if self.request.user.is_authenticated and self.request.user not in challenge.participants.all():
            challenge.participants.add(self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def join(self, request, pk=None):
        """
        Custom action: Add current user to the challenge participants.
        """
        challenge = self.get_object()
        user = request.user
        if user in challenge.participants.all():
            return Response({"detail": "Already joined."}, status=status.HTTP_400_BAD_REQUEST)
        challenge.participants.add(user)
        return Response({"detail": "Successfully joined the challenge."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def leave(self, request, pk=None):
        """
        Custom action: Remove current user from the challenge participants.
        """
        challenge = self.get_object()
        user = request.user
        if user not in challenge.participants.all():
            return Response({"detail": "You are not a participant."}, status=status.HTTP_400_BAD_REQUEST)
        challenge.participants.remove(user)
        return Response({"detail": "Successfully left the challenge."}, status=status.HTTP_200_OK)



class LeaderboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing Leaderboard entries.
    - GET (list/retrieve): open to all.
    - POST/PUT/PATCH/DELETE: authenticated users only.
    """
    serializer_class = LeaderboardSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optionally filter by challenge ID:
        /leaderboards/?challenge=3
        """
        queryset = Leaderboard.objects.all()
        challenge_id = self.request.query_params.get('challenge')
        if challenge_id is not None:
            queryset = queryset.filter(challenge_id=challenge_id)
        return queryset

    def perform_create(self, serializer):
        """
        Automatically assign request.user as the entry's user if none provided.
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def top(self, request):
        """
        Custom endpoint to fetch the top N scores for a given challenge:
        /leaderboards/top/?challenge=3&limit=5
        """
        challenge_id = request.query_params.get('challenge')
        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            return Response(
                {"detail": "limit must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not challenge_id:
            return Response(
                {"detail": "challenge query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        top_entries = (
            Leaderboard.objects
            .filter(challenge_id=challenge_id)
            .order_by('-score')[:limit]
        )
        page = self.paginate_queryset(top_entries)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(top_entries, many=True)
        return Response(serializer.data)



class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing, creating, and updating user profiles.

    - Only authenticated users may interact.
    - Non-staff users see (and edit) only their own profile.
    - Staff may list and retrieve all profiles.
    """
    serializer_class = UserProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = UserProfile.objects.all()
        if not user.is_staff:
            # Non-staff only get their own profile
            return qs.filter(user=user)
        return qs

    def create(self, request, *args, **kwargs):
        # Prevent duplicate profile creation
        if UserProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "A profile for this user already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Assign the logged-in user automatically
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        GET /user_profiles/me/
        Returns the requesting user's profile (create if missing).
        """
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
