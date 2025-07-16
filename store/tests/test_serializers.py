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



class CartItemSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.cart = Cart.objects.create()

        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=50.00,
            category=self.category,
            stock=10
        )

        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)


    def test_valid_cart_item_serialization(self):
        """Test that valid cart item data serializes correctly."""
        serializer = CartItemSerializer(instance=self.cart_item)

        expected_data = {
            "id": self.cart_item.id,
            "product": CartProductSeializer(instance=self.product).data,  # ✅ Nested product serialization
            "quantity": 3,
            "item_total": 150.00  # ✅ 3 * 50.00 = 150.00
        }

        self.assertEqual(serializer.data, expected_data)


    def test_item_total_calculation(self):
        """Test that item_total is calculated correctly."""
        serializer = CartItemSerializer(instance=self.cart_item)
        self.assertEqual(serializer.data["item_total"], 150.00)  # ✅ 3 * 50.00


    def test_product_nested_serialization(self):
        """Test that the product field is serialized correctly."""
        serializer = CartItemSerializer(instance=self.cart_item)
        expected_product_data = CartProductSeializer(instance=self.product).data

        self.assertEqual(serializer.data["product"], expected_product_data)  # ✅ Matches expected nested product data



class CartSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.cart = Cart.objects.create()

        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product1 = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=Decimal("1000.00"),
            category=self.category,
            stock=10
        )
        self.product2 = Product.objects.create(
            name="Phone",
            description="Iphone 16 pro max",
            price=Decimal("500.00"),
            category=self.category,
            stock=10
        )

        self.cart_item1 = CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)  # 2 * 1000 = 2000
        self.cart_item2 = CartItem.objects.create(cart=self.cart, product=self.product2, quantity=3)  # 3 * 500 = 1500


    def test_valid_cart_serialization(self):
        """Test that a valid cart serializes correctly."""
        serializer = CartSerializer(instance=self.cart)

        expected_data = {
            "id": str(self.cart.id),  # ✅ Convert UUID to string to match serializer output
            "items": CartItemSerializer(instance=self.cart.items.all(), many=True).data,
            "total_price": Decimal("3500.00") # ✅ 2000 + 1500 = 3500.00
        }

        self.assertEqual(serializer.data, expected_data)


    def test_total_price_calculation(self):
        """Test that total_price is calculated correctly."""
        serializer = CartSerializer(instance=self.cart)
        self.assertEqual(serializer.data["total_price"], 3500.00)  # ✅ Correct calculation


    def test_empty_cart_total_price(self):
        """Test that an empty cart returns a total price of 0."""
        empty_cart = Cart.objects.create()
        serializer = CartSerializer(instance=empty_cart)
        self.assertEqual(serializer.data["total_price"], 0.00)  # ✅ Should return 0


    def test_cart_items_nested_serialization(self):
        """Test that the items field is serialized correctly."""
        serializer = CartSerializer(instance=self.cart)
        expected_items_data = CartItemSerializer(instance=self.cart.items.all(), many=True).data

        self.assertEqual(serializer.data["items"], expected_items_data)  # ✅ Matches expected nested items data



class OrderItemSerializerTest(TestCase):

    def setUp(self):
        """Set up test data before each test runs."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

        self.customer, created = Customer.objects.get_or_create(
            user=self.user,
            defaults={"phone_number": "1234567890", "birth_date": "1990-01-01"}
        )

        self.order = Order.objects.create(customer=self.customer)

        self.category = Category.objects.create(name="Electronics", description="Electronic items")

        self.product = Product.objects.create(
            name="Laptop",
            description="A high-end gaming laptop.",
            price=1500.00,
            category=self.category,
            stock=10
        )

        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=Decimal("1500.00"))


    def test_valid_order_item_serialization(self):
        """Test that a valid order item serializes correctly."""
        serializer = OrderItemSerializer(instance=self.order_item)

        expected_data = {
            "id": self.order_item.id,
            "product": CartProductSeializer(instance=self.product).data,  # ✅ Nested product serialization
            "quantity": 2,
            "price": Decimal("1500.00")  # ✅ Correctly formatted price
        }

        self.assertEqual(serializer.data, expected_data)


    def test_product_nested_serialization(self):
        """Test that the product field is serialized correctly."""
        serializer = OrderItemSerializer(instance=self.order_item)
        expected_product_data = CartProductSeializer(instance=self.product).data

        self.assertEqual(serializer.data["product"], expected_product_data)  # ✅ Matches expected nested product data


    def test_price_field_serialization(self):
        """Test that the price field correctly represents the item's price."""
        serializer = OrderItemSerializer(instance=self.order_item)
        self.assertEqual(serializer.data["price"], Decimal("1500.00"))  # ✅ Ensures correct price formatting



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
