# from django.urls import path, include

# from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedSimpleRouter

# from .views import ProductViewSet, CartItemViewSet, CartViewSet



# router = DefaultRouter()
# router.register(r'products', ProductViewSet, basename='product')
# router.register(r'carts', CartViewSet, basename='cart')



# # /carts/{cart_pk}/items/
# cart_router = NestedSimpleRouter(router, r'carts', lookup='cart')
# cart_router.register(r'items', CartItemViewSet, basename='cart-items')



# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include(cart_router.urls)),
# ]
