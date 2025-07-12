from rest_framework import viewsets, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Product, CartItem, Cart
from .serializers import ProductSerializer, CartItemSerializer



class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects,
    but allow read-only access to any request.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff



class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    - List/Retrieve: open to all (read-only)
    - Create/Update/Delete: restricted to admin users
    - Supports filtering, search, ordering, and image uploads.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    # Filtering, searching, and ordering
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        'stock': ['exact', 'gte', 'lte'],
        'price': ['exact', 'gte', 'lte'],
    }
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'stock', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        # You could inject extra logic here before saving
        serializer.save()

    def perform_update(self, serializer):
        # Enforce any business rules on update
        serializer.save()
