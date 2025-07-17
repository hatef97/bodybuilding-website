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



class CommentViewSetTest(APITestCase):
    def setUp(self):
        """Set up test dependencies"""
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
        
        # Create a category
        self.category = Category.objects.create(name="Office Supplies")
        
        # Create a product with a valid category
        self.product = Product.objects.create(
            name="Test Product",
            price=50.0,
            stock=10,
            category=self.category  # ✅ Assign a valid category
        )

        # Create comments
        self.comment = Comment.objects.create(
            product=self.product, name=self.regular_user, body="Great product!"
        )

        # Set URLs
        self.comment_list_url = reverse('product-comments-list', kwargs={'product_pk': self.product.pk})
        self.comment_detail_url = reverse('product-comments-detail', kwargs={'product_pk': self.product.pk, 'pk': self.comment.pk})
        
        
    def test_list_comments(self):
        """Test listing comments for a product"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.comment_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one comment exists
        self.assertEqual(response.data[0]['body'], "Great product!")  # Check content


    def test_create_comment_authenticated_user(self):
        """Test that an authenticated user can create a comment"""
        self.client.force_authenticate(user=self.regular_user)

        data = {
                "name": "Test Comment",  
                "body": "This is a test comment",
                "product": self.product.id  
            }
        response = self.client.post(self.comment_list_url, data, format="json")

        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)  # Should have 2 comments now


    def test_create_comment_unauthenticated_user(self):
        """Test that an unauthenticated user cannot create a comment"""
        response = self.client.post(self.comment_list_url, {"body": "Not logged in!"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Should return 401


    def test_admin_can_delete_comment(self):
        """Test that an admin can delete a comment"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.comment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)  # Comment should be deleted


    def test_regular_user_cannot_delete_comment(self):
        """Test that a regular user cannot delete a comment"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.comment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Regular user cannot delete comments
        self.assertEqual(Comment.objects.count(), 1)  # Comment should still exist


    def test_unauthenticated_user_cannot_delete_comment(self):
        """Test that an unauthenticated user cannot delete a comment"""
        response = self.client.delete(self.comment_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Should return 401
        self.assertEqual(Comment.objects.count(), 1)  # Comment should still exist  



class CustomerViewSetTest(APITestCase):
    
    def setUp(self):
        self.client = APIClient()

        # Clear old data before each test
        User.objects.all().delete()
        Customer.objects.all().delete()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )

        # Create regular customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password'
        )

        # Create the Customer first
        self.customer, created = Customer.objects.get_or_create(
            user=self.customer_user
        )

        # Set URLs
        self.customer_list = reverse('customer-list')
        self.customer_me = reverse('customer-me')


    def test_me_get_authenticated(self):
        """Test that an authenticated user can retrieve their customer profile."""
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get(self.customer_me)

        # Ensure request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the response contains customer data
        self.assertEqual(response.data["user"], self.customer_user.id)
        self.assertEqual(response.data["phone_number"], self.customer.phone_number)
        self.assertEqual(response.data["birth_date"], str(self.customer.birth_date) if self.customer.birth_date else None)

    def test_me_put_authenticated(self):
        """Test that an authenticated user can update their customer profile."""
        url = reverse('customer-me')
        self.client.force_authenticate(user=self.customer_user)

        # New data
        updated_data = {
            "phone_number": "987-654-3210",
            "birth_date": "1995-05-15"
        }

        # Send PUT request
        response = self.client.put(url, updated_data)

        # Ensure request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh customer from database
        self.customer.refresh_from_db()

        # Assert changes
        self.assertEqual(self.customer.phone_number, "987-654-3210")
        self.assertEqual(str(self.customer.birth_date), "1995-05-15")


    def test_me_unauthenticated(self):
        """Test that an unauthenticated user cannot access 'me' endpoint."""
        self.client.logout()
        response = self.client.get(self.customer_me)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    
    def test_admin_can_access_customer_list(self):
        """Test that an admin user can access the customer list."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.customer_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    
    def test_non_admin_cannot_access_customer_list(self):
        """Test that a non-admin user cannot access the customer list."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.customer_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class CartItemViewSetTest(APITestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.client = APIClient()

        # Create a user and authenticate
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='password'
        )
        self.client.force_authenticate(user=self.user)

        # Create a cart for the user
        self.cart = Cart.objects.create()

        # Create a category
        self.category = Category.objects.create(name="Office Supplies")
        
        # Create a product 
        self.product = Product.objects.create(
            name="Test Product",
            price=50.0,
            stock=10,
            category=self.category  
        )


        # Create a cart item
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

        # Set URLs for tests
        self.cart_items_url = reverse("cart-items-list", kwargs={"cart_pk": str(self.cart.pk)})
        self.cart_item_detail_url = reverse("cart-items-detail", kwargs={"cart_pk": str(self.cart.pk), "pk": self.cart_item.pk})


    def test_get_cart_items_authenticated(self):
        """Test that an authenticated user can retrieve cart items."""
        response = self.client.get(self.cart_items_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Ensure one item exists in the cart
        self.assertEqual(response.data[0]["product"]["id"], self.product.id)


    def test_add_cart_item_authenticated(self):
        """Test that an authenticated user can add an item to the cart."""
        new_product = Product.objects.create(
            name="Test Product",
            price=50.0,
            stock=10,
            category=self.category  
        )

        payload = {
            "product": new_product.id,
            "quantity": 2
        }

        response = self.client.post(self.cart_items_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 2)


    def test_update_cart_item_authenticated(self):
        """Test that an authenticated user can update the quantity of a cart item."""
        payload = {
            "quantity": 3
        }

        response = self.client.patch(self.cart_item_detail_url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 3)

    def test_delete_cart_item_authenticated(self):
        """Test that an authenticated user can remove an item from their cart."""
        response = self.client.delete(self.cart_item_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(pk=self.cart_item.pk).exists())


    def test_unauthenticated_user_cannot_access_cart(self):
        """Test that an unauthenticated user cannot access cart items."""
        self.client.logout()
        response = self.client.get(self.cart_items_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
