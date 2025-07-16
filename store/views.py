from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView

from .models import Category, Product, PageContent, TeamMember, Customer
from .paginations import DefaultPagination
from .serializers import *
from .permissions import IsAdminOrReadOnly, SendPrivateEmailToCustomerPermission
from .signals import order_created



class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ['name', 'price', 'stock']
    search_fields = ['name']
    pagination_class = DefaultPagination
    queryset = Product.objects.select_related("category")
    
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def destroy(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('category'),
            pk=pk
        )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



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



class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Only the owner of an object may edit it; everyone may read.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only are allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Otherwise, only owner may write
        return obj.user == request.user



class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Cart.
    
    - list:    list current user's carts
    - retrieve: get a single cart with nested items
    - create:  make a new cart (user set from request)
    - update:  change only user (rare) or metadata
    - destroy: delete a cart
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['created_at']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
        # Only show the requesting user's carts,
        # prefetch items + their products to avoid N+1.
        return (
            Cart.objects.filter(user=self.request.user)
                        .prefetch_related(
                            Prefetch(
                                'cart_items',
                                queryset=CartItem.objects.select_related('product')
                            )
                        )
        )

    def perform_create(self, serializer):
        # Tie the new Cart to the current user
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow metadata updates (user may be changed by admin)
        serializer.save()
        