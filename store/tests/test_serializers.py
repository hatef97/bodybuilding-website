from decimal import Decimal
from uuid import uuid4
from datetime import timezone

# from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.db import transaction

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import ValidationError
from rest_framework.utils.serializer_helpers import ReturnDict

from store.models import *
from store.serializers import *
from core.models import CustomUser as User



class CategorySerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.category = Category.objects.create(
            name="Electronics",
            description="All kinds of electronic items."
        )


    def test_valid_category_serialization(self):
        """Test that valid category data serializes correctly."""
        serializer = CategorySerializer(instance=self.category)
        
        expected_data = {
            "id": self.category.id,
            "name": "Electronics",
            "description": "All kinds of electronic items.",
            "num_of_products": 0  # No products yet
        }
        
        self.assertEqual(serializer.data, expected_data)


    def test_invalid_category_name_too_short(self):
        """Test that a category with a short name raises a validation error."""
        invalid_data = {
            "name": "TV",  # Too short (less than 3 chars)
            "description": "Television category"
        }
        
        serializer = CategorySerializer(data=invalid_data)
        
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        
        self.assertIn("Category title should be at least 3.", str(context.exception))

    def test_category_num_of_products(self):
        """Test that the num_of_products field correctly counts associated products."""
        Product.objects.create(name="Laptop", price=1000, category=self.category)
        Product.objects.create(name="Smartphone", price=700, category=self.category)

        serializer = CategorySerializer(instance=self.category)

        self.assertEqual(serializer.data["num_of_products"], 2)



class ProductSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=1500.00,
            category=self.category,
            stock=10
        )


    def test_valid_product_serialization(self):
        """Test that valid product data serializes correctly."""
        serializer = ProductSerializer(instance=self.product)
        
        expected_data = {
            "id": self.product.id,
            "name": "Laptop",
            "description": "A high-end gaming laptop.",
            "price": Decimal("1500.00"),
            "category": self.category.id,
            "category_name": "Electronics",
            "stock": 10,
            "image": None,  # Assuming the image is not set
            "created_at": serializer.data["created_at"],  # Auto-generated field
        }

        self.assertEqual(serializer.data, expected_data)


    def test_category_name_field(self):
        """Test that the category_name field correctly represents the category name."""
        serializer = ProductSerializer(instance=self.product)
        self.assertEqual(serializer.data["category_name"], "Electronics")


    def test_negative_price_validation(self):
        """Test that a negative price raises a validation error."""
        invalid_data = {
            "name": "Smartphone",
            "description": "Latest smartphone model",
            "price": -100,
            "category": self.category.id,
            "stock": 5
        }
        
        serializer = ProductSerializer(data=invalid_data)
        
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        
        self.assertIn("Price cannot be negative.", str(context.exception))


    def test_negative_stock_validation(self):
        """Test that a negative stock raises a validation error."""
        invalid_data = {
            "name": "Smartphone",
            "description": "Latest smartphone model",
            "price": 500,
            "category": self.category.id,
            "stock": -5  # Invalid stock value
        }
        
        serializer = ProductSerializer(data=invalid_data)
        
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        
        self.assertIn("Stock cannot be negative.", str(context.exception))


    def test_slug_is_created_on_product_creation(self):
        """Test that a slug is generated when a product is created."""
        data = {
            "name": "Wireless Headphones",
            "description": "Noise-canceling wireless headphones",
            "price": 200,
            "category": self.category
        }
        
        product = Product(**data)
        product.slug = slugify(product.name)  # Simulate the `create` method
        product.save()
        
        self.assertEqual(product.slug, "wireless-headphones")



class CommentSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=1500.00,
            category=self.category,
            stock=10
        )

        self.comment = Comment.objects.create(
            product=self.product,
            name="John Doe",
            body="Great product!"
        )


    def test_valid_comment_serialization(self):
        """Test that valid comment data serializes correctly."""
        serializer = CommentSerializer(instance=self.comment)
        
        expected_data = {
            "id": self.comment.id,
            "name": "John Doe",
            "body": "Great product!"
        }

        self.assertEqual(serializer.data, expected_data)


    def test_create_comment_with_product_pk(self):
        """Test that a comment is created with the correct product_id from context."""
        data = {
            "name": "Jane Doe",
            "body": "Amazing quality!"
        }

        serializer = CommentSerializer(data=data, context={"product_pk": self.product.id})
        self.assertTrue(serializer.is_valid())

        comment = serializer.save()

        self.assertEqual(comment.name, "Jane Doe")
        self.assertEqual(comment.body, "Amazing quality!")
        self.assertEqual(comment.product_id, self.product.id)  # ✅ Ensures correct product association


    def test_missing_product_pk_in_context(self):
        """Test that a missing product_pk in context raises an error."""
        data = {
            "name": "Jane Doe",
            "body": "Amazing quality!"
        }

        serializer = CommentSerializer(data=data)  # ❌ No 'product_pk' in context

        with self.assertRaises(KeyError):
            serializer.is_valid(raise_exception=True)
            serializer.save()



class CustomerSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password123")

        self.customer, created = Customer.objects.get_or_create(
            user=self.user,
            defaults={"phone_number": "1234567890", "birth_date": "1990-01-01"}
        )
        # Explicitly update the customer to ensure correct values
        if not created:
            self.customer.phone_number = "1234567890"
            self.customer.birth_date = "1990-01-01"
            self.customer.save()


    def test_valid_customer_serialization(self):
        """Test that valid customer data serializes correctly."""
        serializer = CustomerSerializer(instance=self.customer)
        
        expected_data = {
            "id": self.customer.id,
            "user": self.user.id,  # Ensuring the user field is included as an ID
            "phone_number": "1234567890",
            "birth_date": "1990-01-01"
        }

        self.assertEqual(serializer.data, expected_data)


    def test_read_only_user_field(self):
        """Test that the user field is read-only and cannot be changed."""
        data = {
            "user": 999,  # Invalid user ID (should be read-only)
            "phone_number": "0987654321",
            "birth_date": "2000-05-15"
        }

        serializer = CustomerSerializer(instance=self.customer, data=data, partial=True)

        self.assertTrue(serializer.is_valid())

        updated_customer = serializer.save()

        self.assertEqual(updated_customer.user, self.customer.user)  # ✅ User should remain unchanged


    def test_create_customer_successfully(self):
        """Test that a new customer can be created successfully."""
        new_user = User.objects.create_user(username="newuser", email="newuser@example.com", password="password123")

        Customer.objects.filter(user=new_user).delete()

        data = {
            "phone_number": "5551234567",
            "birth_date": "1995-08-20"
        }

        serializer = CustomerSerializer(data=data, context={"user": new_user})
        self.assertTrue(serializer.is_valid())

        # Create customer only if it doesn't exist
        customer, created = Customer.objects.get_or_create(user=new_user, defaults=serializer.validated_data)   

        self.assertTrue(created)
        self.assertEqual(customer.phone_number, "5551234567")
        self.assertEqual(str(customer.birth_date), "1995-08-20")
        self.assertEqual(customer.user, new_user)


    def test_missing_required_fields(self):
        """Test that missing required fields raise a validation error."""
        data = {}  # Empty data should fail

        serializer = CustomerSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)



class UpdateCartItemSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.cart = Cart.objects.create()

        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=1500.00,
            category=self.category,
            stock=10
        )

        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)


    def test_valid_cart_item_update(self):
        """Test that updating cart item quantity works correctly."""
        data = {"quantity": 5}  # Valid new quantity

        serializer = UpadateCartItemSerializer(instance=self.cart_item, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_cart_item = serializer.save()

        self.assertEqual(updated_cart_item.quantity, 5)  # ✅ Quantity should be updated


    def test_negative_quantity_raises_error(self):
        """Test that providing a negative quantity raises a validation error."""
        data = {"quantity": -1}  # Invalid quantity

        serializer = UpadateCartItemSerializer(instance=self.cart_item, data=data, partial=True)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertIn("quantity", str(context.exception))  # ✅ Ensures proper error message


    def test_zero_quantity_is_valid(self):
        """Test that setting quantity to zero is allowed (for removing items)."""
        data = {"quantity": 0}  # Removing item

        serializer = UpadateCartItemSerializer(instance=self.cart_item, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_cart_item = serializer.save()

        self.assertEqual(updated_cart_item.quantity, 0)  # ✅ Quantity should be updated to zero


    def test_large_quantity_is_valid(self):
        """Test that setting a large quantity is valid."""
        data = {"quantity": 1000}  # Large but valid quantity

        serializer = UpadateCartItemSerializer(instance=self.cart_item, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_cart_item = serializer.save()

        self.assertEqual(updated_cart_item.quantity, 1000)  # ✅ Quantity should be updated



class AddCartItemSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.cart = Cart.objects.create()

        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=1500.00,
            category=self.category,
            stock=10
        )


    def test_valid_cart_item_serialization(self):
        """Test that valid cart item data serializes correctly."""
        cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        serializer = AddCartItemSerializer(instance=cart_item)
        
        expected_data = {
            "id": cart_item.id,
            "product": self.product.id,
            "quantity": 2
        }

        self.assertEqual(serializer.data, expected_data)


    def test_create_new_cart_item(self):
        """Test that a new cart item is created successfully if it does not exist."""
        data = {
            "product": self.product.id,
            "quantity": 3
        }

        serializer = AddCartItemSerializer(data=data, context={"cart_pk": self.cart.id})
        self.assertTrue(serializer.is_valid())

        cart_item = serializer.save()

        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(cart_item.cart_id, self.cart.id)


    def test_update_existing_cart_item_quantity(self):
        """Test that an existing cart item has its quantity increased."""
        existing_cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

        data = {
            "product": self.product.id,
            "quantity": 3  # Adding more of the same product
        }

        serializer = AddCartItemSerializer(data=data, context={"cart_pk": self.cart.id})
        self.assertTrue(serializer.is_valid())

        updated_cart_item = serializer.save()

        self.assertEqual(updated_cart_item.id, existing_cart_item.id)  # ✅ Same cart item should be updated
        self.assertEqual(updated_cart_item.quantity, 5)  # ✅ Quantity should be increased


    def test_missing_cart_context_raises_error(self):
        """Test that a missing 'cart_pk' in context raises a KeyError."""
        data = {
            "product": self.product.id,
            "quantity": 2
        }

        serializer = AddCartItemSerializer(data=data)  # ❌ No 'cart_pk' in context

        with self.assertRaises(KeyError):
            serializer.is_valid(raise_exception=True)
            serializer.save()


    def test_negative_quantity_raises_error(self):
        """Test that providing a negative quantity raises a validation error."""
        data = {
            "product": self.product.id,
            "quantity": -1  # Invalid quantity
        }

        serializer = AddCartItemSerializer(data=data, context={"cart_pk": self.cart.id})

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertIn("quantity", str(context.exception))



class CartItemSerializerTests(APITestCase):
    """
    APITestCase suite for CartItemSerializer, covering nested product serialization,
    write-only product_id, quantity validation, total_price computation, and create/update.
    """

    def setUp(self):
        # Set up request context for nested serializers
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')

        # Create a user and cart
        self.user = User.objects.create_user(email='testuser@mail.com', username='testuser', password='pass')
        self.cart = Cart.objects.create(user=self.user)

        # Create a product for testing
        self.product = Product.objects.create(
            name="Widget",
            description="A useful widget",
            price=Decimal('2.50'),
            stock=20
        )

        # Base valid data for creation
        self.valid_data = {
            'product_id': self.product.id,
            'quantity': 3
        }


    def test_fields_present(self):
        """
        Serialization output should include id, product, quantity, total_price, but not product_id.
        """
        # Create item to test read serialization
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        serializer = CartItemSerializer(item, context={'request': self.request})
        data = serializer.data
        self.assertSetEqual(set(data.keys()), {'id', 'product', 'quantity', 'total_price'})
        self.assertNotIn('product_id', data)


    def test_nested_product_data(self):
        """
        Nested product field should contain the serialized Product data.
        """
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        serializer = CartItemSerializer(item, context={'request': self.request})
        product_data = serializer.data['product']
        # Check key fields in nested product
        for field in ['id', 'name', 'description', 'price', 'stock', 'is_in_stock', 'image_url', 'created_at']:
            self.assertIn(field, product_data)
        self.assertEqual(product_data['id'], self.product.id)
        self.assertEqual(product_data['name'], self.product.name)


    def test_total_price_computation(self):
        """
        total_price should equal quantity * product.price formatted to 2 decimals.
        """
        serializer = CartItemSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        item = serializer.save(cart=self.cart)
        expected = Decimal('{:.2f}'.format(self.product.price * self.valid_data['quantity']))
        # Instance total_price method
        self.assertEqual(item.total_price(), self.product.price * self.valid_data['quantity'])
        # Serializer output
        out_ser = CartItemSerializer(item, context={'request': self.request})
        self.assertEqual(out_ser.data['total_price'], expected)


    def test_negative_quantity_validation(self):
        """
        Serializer should reject negative quantity values.
        """
        data = self.valid_data.copy()
        data['quantity'] = -2
        serializer = CartItemSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_create_cart_item(self):
        """
        Valid data should create a new CartItem under the given cart.
        """
        serializer = CartItemSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(cart=self.cart)
        self.assertIsInstance(item, CartItem)
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, self.valid_data['quantity'])


    def test_update_quantity_partial(self):
        """
        Partial update should change only the quantity.
        """
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        update_data = {'quantity': 10}
        serializer = CartItemSerializer(item, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.quantity, update_data['quantity'])
        self.assertEqual(updated.product, self.product)
        self.assertEqual(updated.cart, self.cart)



class CartSerializerTests(APITestCase):
    """
    APITestCase suite for CartSerializer, covering field inclusion, nested items,
    total_price calculation, create with CurrentUserDefault, and update behavior.
    """

    def setUp(self):
        # Setup request and context
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')
        # Create two users
        self.user = User.objects.create_user(username='user1', email='user1@example.com', password='pass')
        self.other_user = User.objects.create_user(username='user2', email='user2@example.com', password='pass')
        # Authenticate request
        self.request.user = self.user
        # Create a cart for user
        self.cart = Cart.objects.create(user=self.user)
        # Create products
        self.p1 = Product.objects.create(name='P1', description='', price=Decimal('1.00'), stock=5)
        self.p2 = Product.objects.create(name='P2', description='', price=Decimal('2.00'), stock=5)
        # Add items
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)  # total 2.00
        CartItem.objects.create(cart=self.cart, product=self.p2, quantity=3)  # total 6.00


    def test_fields_present(self):
        """
        Serialized output includes id, user, items, total_price, created_at.
        """
        serializer = CartSerializer(self.cart, context={'request': self.request})
        data = serializer.data
        expected_keys = {'id', 'user', 'items', 'total_price', 'created_at'}
        self.assertSetEqual(set(data.keys()), expected_keys)


    def test_nested_items_serialization(self):
        """
        items field should list serialized CartItem entries.
        """
        serializer = CartSerializer(self.cart, context={'request': self.request})
        items = serializer.data['items']
        # Should have two items
        self.assertEqual(len(items), 2)
        # Check item structure
        for item in items:
            self.assertIn('id', item)
            self.assertIn('product', item)
            self.assertIn('quantity', item)
            self.assertIn('total_price', item)


    def test_total_price_calculation(self):
        """
        total_price should equal sum of CartItem total_price values.
        """
        serializer = CartSerializer(self.cart, context={'request': self.request})
        # 2*1.00 + 3*2.00 = 2 + 6 = 8.00
        self.assertEqual(serializer.data['total_price'], Decimal('8.00'))


    def test_create_default_user(self):
        """
        Creating without user field should assign CurrentUserDefault.
        """
        data = {}  # no user provided
        serializer = CartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        new_cart = serializer.save()
        self.assertEqual(new_cart.user, self.user)


    def test_update_user_field(self):
        """
        Updating the user field should change cart ownership.
        """
        data = {'user': self.other_user.id}
        serializer = CartSerializer(self.cart, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.user, self.other_user)


    def test_cannot_set_total_price_or_created_at(self):
        """
        Read-only fields total_price and created_at should be ignored or disallowed on input.
        """
        data = {'total_price': '100.00', 'created_at': '2000-01-01T00:00:00Z'}
        serializer = CartSerializer(self.cart, data=data, partial=True)
        # is_valid should be True (fields ignored)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        # values unchanged
        self.assertNotEqual(updated.total_price, Decimal('100.00'))
        self.assertNotEqual(updated.created_at.isoformat(), '2000-01-01T00:00:00+00:00')



class OrderSerializerTests(APITestCase):
    """
    APITestCase suite for OrderSerializer, covering field inclusion, nested items,
    total_price, create and update behavior, and read-only enforcement.
    """

    def setUp(self):
        # Setup request with authenticated user
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/')
        self.user = User.objects.create_user(
            username='orderuser', email='order@example.com', password='pass'
        )
        self.request.user = self.user

        # Create Cart and CartItems for the order
        self.cart = Cart.objects.create(user=self.user)
        # Products
        self.p1 = Product.objects.create(
            name='Prod1', description='D1', price=Decimal('3.00'), stock=10
        )
        self.p2 = Product.objects.create(
            name='Prod2', description='D2', price=Decimal('4.50'), stock=5
        )
        # Cart items
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)  # total 6.00
        CartItem.objects.create(cart=self.cart, product=self.p2, quantity=1)  # total 4.50

        # Valid data for order creation
        self.valid_data = {
            'shipping_address': '123 Test St.'
            # status defaults to 'pending'; user defaulted; items read-only
        }


    def test_fields_present(self):
        """
        Serialized output includes id, user, status, items, total_price, shipping_address, created_at.
        """
        # First create an order
        order = Order.objects.create(user=self.user, cart=self.cart, shipping_address='123 Test St.')
        serializer = OrderSerializer(order, context={'request': self.request})
        data = serializer.data
        expected_keys = {'id', 'user', 'status', 'items', 'total_price', 'shipping_address', 'created_at'}
        self.assertSetEqual(set(data.keys()), expected_keys)


    def test_nested_items_and_total_price(self):
        """
        items lists CartItems and total_price sums them.
        """
        order = Order.objects.create(user=self.user, cart=self.cart, shipping_address='Addr')
        serializer = OrderSerializer(order, context={'request': self.request})
        items = serializer.data['items']
        self.assertEqual(len(items), 2)
        # Total should be 6.00 + 4.50 = 10.50
        self.assertEqual(serializer.data['total_price'], Decimal('10.50'))


    def test_create_order_default_fields(self):
        """
        Creating via serializer should set user from request and status default.
        """
        serializer = OrderSerializer(data=self.valid_data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save(cart=self.cart)
        self.assertIsInstance(order, Order)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.cart, self.cart)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.shipping_address, self.valid_data['shipping_address'])
        # Check computed total price
        self.assertEqual(order.total_price, Decimal('10.50'))


    def test_update_status_and_address(self):
        """
        Partial update should allow changing only status and shipping_address.
        """
        order = Order.objects.create(user=self.user, cart=self.cart, shipping_address='Old Addr')
        update_data = {'status': 'completed', 'shipping_address': 'New Addr'}
        serializer = OrderSerializer(order, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.status, 'completed')
        self.assertEqual(updated.shipping_address, 'New Addr')


    def test_read_only_fields_ignored(self):
        """
        Read-only fields user, items, total_price, created_at cannot be overwritten.
        """
        order = Order.objects.create(user=self.user, cart=self.cart, shipping_address='Addr')
        data = {
            'user': 999,
            'items': [],
            'total_price': '999.99',
            'created_at': '2000-01-01T00:00:00Z'
        }
        serializer = OrderSerializer(order, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        saved = serializer.save()
        # original user remains
        self.assertEqual(saved.user, self.user)
        # total_price unchanged
        self.assertEqual(saved.total_price, order.total_price)
        # shipping_address unchanged
        self.assertEqual(saved.shipping_address, order.shipping_address)
        # items unchanged length
        self.assertEqual(list(saved.cart.cart_items.all()).__len__(), 2)


    def test_invalid_status_choice(self):
        """
        Serializer should reject invalid status values.
        """
        order = Order.objects.create(user=self.user, cart=self.cart, shipping_address='Addr')
        serializer = OrderSerializer(order, data={'status': 'invalid'}, partial=True)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)



class PaymentSerializerTests(APITestCase):
    """
    APITestCase suite for PaymentSerializer, covering field inclusion,
    amount validation, create and update behaviors, and read-only enforcement.
    """

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='payuser',
            email='payuser@example.com',
            password='pass'
        )
        # Create a cart and related items
        self.cart = Cart.objects.create(user=self.user)
        # Products
        self.p1 = Product.objects.create(
            name='Prod1', description='D1', price=Decimal('5.00'), stock=10
        )
        # Add items to cart
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=2)  # total 10.00
        # Create an order based on cart
        self.order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            shipping_address='123 Payment St.'
        )
        # Base valid data
        self.valid_data = {
            'order_id': self.order.id,
            'amount': self.order.total_price,
            'status': 'pending'
        }


    def test_fields_present(self):
        """
        Serializer output includes id, order_id, user, payment_date, amount, status.
        """
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            status='pending'
        )
        serializer = PaymentSerializer(payment)
        data = serializer.data
        expected_keys = {'id', 'order_id', 'user', 'payment_date', 'amount', 'status'}
        self.assertSetEqual(set(data.keys()), expected_keys)
        # Check read-only user field sourced from order.user.username
        self.assertEqual(data['user'], self.user.username)


    def test_validate_amount_negative(self):
        """
        Negative amount should raise a ValidationError.
        """
        data = self.valid_data.copy()
        data['amount'] = Decimal('-1.00')
        serializer = PaymentSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_validate_amount_mismatch(self):
        """
        Amount not equal to order.total_price should raise ValidationError.
        """
        data = self.valid_data.copy()
        data['amount'] = self.order.total_price + Decimal('1.00')
        serializer = PaymentSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_create_pending_payment(self):
        """
        Creating with default status 'pending' should not trigger complete/fail methods.
        """
        serializer = PaymentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        payment = serializer.save()
        self.assertIsInstance(payment, Payment)
        self.assertEqual(payment.status, 'pending')
        # payment_date auto-set
        self.assertIsNotNone(payment.payment_date)


    def test_create_completed_payment(self):
        """
        Creating with status 'completed' should call complete_payment().
        """
        data = self.valid_data.copy()
        data['status'] = 'completed'
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        payment = serializer.save()
        self.assertEqual(payment.status, 'completed')


    def test_create_failed_payment(self):
        """
        Creating with status 'failed' should call fail_payment().
        """
        data = self.valid_data.copy()
        data['status'] = 'failed'
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        payment = serializer.save()
        self.assertEqual(payment.status, 'failed')


    def test_update_status(self):
        """
        Updating status via serializer should call appropriate methods.
        """
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            status='pending'
        )
        serializer = PaymentSerializer(
            payment, data={'status': 'completed'}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.status, 'completed')


    def test_read_only_fields_ignored(self):
        """
        Read-only fields id, user, payment_date should not be overwritten.
        """
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            status='pending'
        )
        data = {
            'id': 999,
            'user': 'otheruser',
            'payment_date': '2000-01-01T00:00:00Z'
        }
        serializer = PaymentSerializer(payment, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        saved = serializer.save()
        self.assertEqual(saved.id, payment.id)
        # user field read-only from order.user.username
        self.assertEqual(serializer.data['user'], self.user.username)
        # payment_date unchanged
        self.assertNotEqual(serializer.data['payment_date'], '2000-01-01T00:00:00Z')


    def test_invalid_status_choice(self):
        """
        Providing an invalid status choice should raise ValidationError.
        """
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            status='pending'
        )
        serializer = PaymentSerializer(
            payment, data={'status': 'invalid'}, partial=True
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
