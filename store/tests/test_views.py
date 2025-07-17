from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils.timezone import now

from store.models import *
from store.serializers import CustomerSerializer, CartItemSerializer, OrderSerializer
from core.models import CustomUser as User



class ProductViewSetTest(APITestCase):

    def setUp(self):       
        # create users
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )

        # create data
        self.category = Category.objects.create(name="Stationery")
        self.product = Product.objects.create(
            name="Smartphone",
            description="Latest smartphone with high specs",
            price=599.99,
            category=self.category,
            stock=50,
            created_at=now(),
        )

        # single client instance
        self.client = APIClient()
        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse("product-detail", kwargs={"pk": self.product.id})
    
    
    def test_list_products(self):
        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Pagination response
    
    
    def test_retrieve_product(self):
        """Test retrieving a single product."""
        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    
    def test_admin_can_create_product(self):
        """Test that an admin user can create a product"""
        self.client.force_authenticate(user=self.admin_user)  # ✅ Authenticate Admin

        product_data = {
            "name": "New Product",
            "description": "A test product",
            "price": 19.99,
            "category": self.category.id,  # ✅ Pass category ID
            "stock": 10,
        }

        response = self.client.post(self.product_list_url, product_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # ✅ Expect success


    def test_admin_can_update_product(self):
        """✅ Admin user can update a product."""
        self.client.force_authenticate(user=self.admin_user)  # ✅ Authenticate Admin

        update_data = {
            "name": "Updated Product",
            "description": "Updated Description",
            "price": 59.99,
            "category": self.category.id,
            "stock": 5,
        }

        response = self.client.put(self.product_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], update_data["name"])


    def test_admin_can_delete_product(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())


    def test_regular_user_cannot_create_product(self):
        """❌ Regular (non-admin) user cannot create a product."""
        self.client.force_authenticate(user=self.regular_user)

        product_data = {
            "name": "Forbidden Product",
            "description": "A test product",
            "price": 19.99,
            "category": self.category.id,
            "stock": 10,
        }


    def test_regular_user_cannot_update_product(self):
        """❌ Regular (non-admin) user cannot update a product."""
        self.client.force_authenticate(user=self.regular_user)

        update_data = {
            "name": "Unauthorized Update",
            "description": "Updated Description",
            "price": 59.99,
            "category": self.category.id,
            "stock": 5,
        }

        response = self.client.put(self.product_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_regular_user_cannot_delete_product(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_cannot_create_product(self):
        """❌ Unauthenticated user cannot create a product."""
        self.client.force_authenticate(user=None)
        product_data = {
            "name": "Unauthorized Product",
            "description": "A test product",
            "price": 19.99,
            "category": self.category.id,
            "stock": 10,
        }

        response = self.client.post(self.product_list_url, product_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_unauthenticated_user_cannot_delete_product(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_search_products_by_name(self):
        """✅ Search products by name."""
        response = self.client.get(f"{self.product_list_url}?search=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_order_products_by_price(self):
        """✅ Order products by price."""
        response = self.client.get(f"{self.product_list_url}?ordering=price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
