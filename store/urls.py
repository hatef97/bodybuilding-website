from rest_framework_nested import routers

from django.urls import path

from . import views



router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'cutomers', views.CustomerViewSet, basename='customer')
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')


product_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
product_router.register(r'products', views.ProductViewSet, basename='category-products')

cart_items_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_items_router.register('items', views.CartItemViewSet, basename='cart-items')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comments')


urlpatterns = router.urls + products_router.urls + cart_items_router.urls + product_router.urls
