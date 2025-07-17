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



class CategoryViewSetTest(APITestCase):

    def setUp(self):
        """Set up test data."""
        # adjust to pass only email & password (and any required extra_fields)
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='password'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='password'
        )

        self.category1 = Category.objects.create(name="Electronics")
        self.category2 = Category.objects.create(name="Books")

        self.category_list_url   = reverse('category-list')
        self.category_detail_url = reverse(
            'category-detail',
            kwargs={'pk': self.category1.pk}
        )


    def test_list_categories(self):
        """✅ Test retrieving the list of categories."""
        response = self.client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)


    def test_retrieve_category(self):
        """✅ Test retrieving a single category."""
        response = self.client.get(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category1.name)


    def test_admin_can_create_category(self):
        """✅ Test that an admin user can create a category."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Fashion"}
        response = self.client.post(self.category_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name="Fashion").exists())


    def test_non_admin_cannot_create_category(self):
        """❌ Test that a regular user cannot create a category."""
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "Fashion"}
        response = self.client.post(self.category_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_can_update_category(self):
        """✅ Test that an admin user can update a category."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Updated Electronics"}
        response = self.client.put(self.category_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.name, "Updated Electronics")


    def test_non_admin_cannot_update_category(self):
        """❌ Test that a regular user cannot update a category."""
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "Updated Electronics"}
        response = self.client.put(self.category_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_cannot_delete_category_with_products(self):
        """❌ Test that a category with products cannot be deleted."""
        Product.objects.create(name="Laptop", category=self.category1, price=1000, stock=10)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('Cannot delete category with existing products. Remove products first.', response.data['error'])


    def test_admin_can_delete_empty_category(self):
        """✅ Test that an admin user can delete a category without products."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category1.pk).exists())


    def test_non_admin_cannot_delete_category(self):
        """❌ Test that a regular user cannot delete a category."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
