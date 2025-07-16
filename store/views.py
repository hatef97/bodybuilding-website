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

from .models import *
from .paginations import DefaultPagination
from .serializers import *
from .permissions import IsAdminOrReadOnly
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



class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related('products').all()
    permission_classes = [IsAdminOrReadOnly]
    

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, pk=None):
        category = get_object_or_404(Category, pk=pk)
        if category.products.exists():
            return Response(
                {'error': 'Cannot delete category with existing products. Remove products first.'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().destroy(request, pk)



class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        product_pk = self.kwargs['product_pk']
        return Comment.objects.filter(product_id=product_pk)

    def get_serializer_context(self):
        return {'product_pk': self.kwargs['product_pk']}
    
    def destroy(self, request, *args, **kwargs):
        product_pk = kwargs.get('product_pk')  # Get product ID from URL
        pk = kwargs.get('pk')  # Get comment ID

        # Ensure the comment belongs to the correct product
        comment = get_object_or_404(Comment, pk=pk, product_id=product_pk)
        
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                            status=status.HTTP_403_FORBIDDEN
                            )
        
        comment.delete()
        return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAdminUser]
    
    
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.user.id
        customer = Customer.objects.get(user_id=user_id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)



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
        