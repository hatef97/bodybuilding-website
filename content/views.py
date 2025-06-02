from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from .models import Article
from .serializers import ArticleSerializer



class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission: 
    - SAFE_METHODS (GET, HEAD, OPTIONS) are allowed for any user.
    - Non‐safe methods (POST, PUT, PATCH, DELETE) are allowed only if request.user is:
      1) the article’s author, or 
      2) a staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        # Always allow safe methods
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the author or staff
        return obj.author == request.user or request.user.is_staff



class ArticleViewSet(viewsets.ModelViewSet):
    """
      - Uses `slug` as the lookup field for detail URLs.
      - Allows filtering by author username, status, and is_published.
      - Supports search on title, excerpt, and content.
      - Supports ordering by published_at and created_at.
      - Only authors (or staff) can modify an article; everyone else can read.
    """

    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer
    lookup_field = "slug"

    # Only authenticated users can create/edit; unauthenticated users can read
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    # Filtering, searching, and ordering support
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "author__username",  # e.g. ?author__username=johndoe
        "status",            # e.g. ?status=published
        "is_published",      # e.g. ?is_published=True
    ]
    search_fields = [
        "title",
        "excerpt",
        "content",
    ]
    ordering_fields = [
        "published_at",
        "created_at",
        "title",
    ]
    ordering = ["-published_at", "-created_at"]

    def perform_create(self, serializer):
        """
        Override to ensure `author` is set to request.user if none provided,
        and to populate `published_at` if publishing immediately.
        """
        author = self.request.user
        is_published = serializer.validated_data.get("is_published", False)

        # If the client did not explicitly set author_id, use request.user
        serializer.save(author=author, published_at=timezone.now() if is_published else None)

    def perform_update(self, serializer):
        """
        Override to ensure that if `is_published` switches from False → True and
        no `published_at` was provided, we set `published_at` now.
        """
        instance = serializer.instance
        new_is_published = serializer.validated_data.get("is_published", instance.is_published)
        new_published_at = serializer.validated_data.get("published_at", instance.published_at)

        # If going from draft → published without an explicit timestamp, set now
        if not instance.is_published and new_is_published and not new_published_at:
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def recent(self, request):
        """
        Custom endpoint: `/api/articles/recent/`
        Returns the 5 most recently published articles (is_published=True),
        ordered by published_at descending.
        """
        recent_qs = Article.published.order_by("-published_at")[:5]
        page = self.paginate_queryset(recent_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recent_qs, many=True, context={"request": request})
        return Response(serializer.data)
