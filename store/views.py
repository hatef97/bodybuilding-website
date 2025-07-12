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



class IsOwnerOfCart(permissions.BasePermission):
    """
    Permission that only allows owners of a cart to manage its items.
    """
    def has_permission(self, request, view):
        cart_pk = view.kwargs.get('cart_pk')
        if not cart_pk:
            return False
        cart = get_object_or_404(Cart, pk=cart_pk)
        return cart.user == request.user

    def has_object_permission(self, request, view, obj):
        # obj is a CartItem
        return obj.cart.user == request.user



class CartItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CartItem, nested under Cart.
    
    - list/retrieve: view items in your cart
    - create: add a product + quantity to your cart
    - update/partial_update: change quantity
    - destroy: remove item
    """
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOfCart]
    parser_classes = [JSONParser]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product__id', 'quantity']
    ordering_fields = ['quantity', 'total_price']
    ordering = ['-id']

    def get_cart(self):
        # Lookup the cart by URL, ensure it belongs to current user
        return get_object_or_404(Cart, pk=self.kwargs['cart_pk'], user=self.request.user)

    def get_queryset(self):
        # Only items in the specified cart, with product prefetched
        return (
            CartItem.objects
            .filter(cart=self.get_cart())
            .select_related('product')
        )

    def perform_create(self, serializer):
        # Associate the new item with the cart from the URL
        serializer.save(cart=self.get_cart())

    def perform_update(self, serializer):
        # Only quantity can change; cart/product remain fixed by serializer
        serializer.save()
