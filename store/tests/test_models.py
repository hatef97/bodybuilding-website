from decimal import Decimal
import datetime
from datetime import date
import uuid

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from store.models import *
from core.models import CustomUser as User



class ProductModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="All kinds of electronics"
        )

        self.discount1 = Discount.objects.create(
            discount=10.0,
            description="Spring Sale"
        )

        self.discount2 = Discount.objects.create(
            discount=15.0,
            description="Holiday Discount"
        )

        self.product = Product.objects.create(
            name="Smartphone",
            description="Latest smartphone with high specs",
            price=599.99,
            category=self.category,
            stock=50,
            created_at=now(),
        )

        self.product.discounts.add(self.discount1, self.discount2)

    def test_product_creation(self):
        """Test product instance is created correctly."""
        self.assertEqual(self.product.name, "Smartphone")
        self.assertEqual(self.product.description, "Latest smartphone with high specs")
        self.assertEqual(self.product.price, 599.99)
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.stock, 50)

    def test_string_representation(self):
        """Test the __str__ method of Product."""
        self.assertEqual(str(self.product), "Smartphone")

    def test_category_relationship(self):
        """Test that product is linked to the correct category."""
        self.assertEqual(self.product.category.name, "Electronics")

    def test_discounts_relationship(self):
        """Test the many-to-many relationship with Discount."""
        discounts = self.product.discounts.all()
        self.assertEqual(discounts.count(), 2)
        self.assertIn(self.discount1, discounts)
        self.assertIn(self.discount2, discounts)

    def test_image_field_blank(self):
        """Test that image field can be left blank."""
        self.assertFalse(self.product.image)

    def test_image_upload(self):
        """Test uploading an image to the product."""
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        self.product.image = image
        self.product.save()
        self.assertTrue(self.product.image.name.startswith('products/test_image'))

    def test_default_stock(self):
        """Test stock default value."""
        product_without_stock = Product.objects.create(
            name="Tablet",
            description="High performance tablet",
            price=299.99,
            category=self.category
        )
        self.assertEqual(product_without_stock.stock, 0)

    def test_created_at_auto_now_add(self):
        """Test created_at is set on creation."""
        self.assertIsNotNone(self.product.created_at)



class CartModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="testuser@mail.com", username="testuser", password="pass1234")
        self.cart = Cart.objects.create(user=self.user)

        self.product1 = Product.objects.create(
            name="Protein Bar",
            description="A tasty protein bar",
            price=Decimal("2.50"),
            stock=100,
        )
        self.product2 = Product.objects.create(
            name="Whey Protein",
            description="5lb whey protein tub",
            price=Decimal("49.99"),
            stock=50,
        )

        self.cart_item1 = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=4,
        )

        self.cart_item2 = CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=1,
        )


    def test_cart_str_representation(self):
        self.assertEqual(str(self.cart), f"Cart of {self.user}")


    def test_cart_created_at_auto_now_add(self):
        self.assertIsNotNone(self.cart.created_at)
        self.assertLessEqual(self.cart.created_at, timezone.now())


    def test_cart_relationship_with_user(self):
        self.assertEqual(self.cart.user, self.user)


    def test_cart_items_relationship(self):
        self.assertEqual(self.cart.products.count(), 2)
        self.assertIn(self.product1, self.cart.products.all())
        self.assertIn(self.product2, self.cart.products.all())


    def test_total_price_calculation(self):
        expected_total = (
            self.product1.price * self.cart_item1.quantity +
            self.product2.price * self.cart_item2.quantity
        )
        self.assertEqual(self.cart.total_price(), expected_total)


    def test_cartitem_total_price_method(self):
        self.assertEqual(self.cart_item1.total_price(), Decimal("10.00"))  # 4 x 2.50
        self.assertEqual(self.cart_item2.total_price(), Decimal("49.99"))  # 1 x 49.99


    def test_cart_empty_total_price(self):
        empty_cart = Cart.objects.create(user=self.user)
        self.assertEqual(empty_cart.total_price(), 0)



class CartItemModelTest(TestCase):

    def setUp(self):
        # Create a test user for associating with Cart instances
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            password="password123"
        )
        # Create a Product with known attributes for predictable behavior
        self.product = Product.objects.create(
            name="Test Product",
            description="A product for testing",
            price=Decimal("9.99"),  # Decimal ensures accurate currency calculations
            stock=100  # Initial inventory level
        )
        # Instantiate a Cart linked to the test user
        self.cart = Cart.objects.create(user=self.user)
        # Create a CartItem associating the cart and product with a set quantity
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3  # Quantity used for price calculation tests
        )


    def test_str_returns_product_name_and_quantity(self):
        # __str__ should reflect "<product name> x <quantity>"
        expected = f"{self.product.name} x {self.cart_item.quantity}"
        self.assertEqual(str(self.cart_item), expected)


    def test_total_price_calculation(self):
        # total_price() multiplies product.price by quantity
        expected_total = self.product.price * self.cart_item.quantity
        self.assertEqual(self.cart_item.total_price(), expected_total)


    def test_zero_quantity_and_total_price_zero(self):
        # Edge case: zero quantity should yield zero total price
        zero_item = CartItem(cart=self.cart, product=self.product, quantity=0)
        self.assertEqual(zero_item.total_price(), Decimal("0"))


    def test_negative_quantity_validation(self):
        # CartItem.quantity is PositiveIntegerField; negative values should fail validation
        negative_item = CartItem(cart=self.cart, product=self.product, quantity=-1)
        with self.assertRaises(ValidationError):
            negative_item.full_clean()


    def test_deleting_product_cascades_to_cart_item(self):
        # Deleting the Product should cascade delete associated CartItem(s)
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.product.delete()
        with self.assertRaises(CartItem.DoesNotExist):
            CartItem.objects.get(pk=item.pk)


    def test_cart_relationship(self):
        # Verify that the cart's reverse relation returns our CartItem
        items = self.cart.cart_items.all()
        self.assertIn(self.cart_item, items)



class OrderModelTest(TestCase):

    def setUp(self):
        # Create a user and customer for the order
        self.user = User.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            password='testpassword123'
        )
        Customer.objects.filter(user=self.user).delete()
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number="123-456-7890"
        )

        # Create an order instance
        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.ORDER_STATUS_UNPAID
        )

    def test_order_creation(self):
        """Test that an Order instance is created correctly."""
        self.assertEqual(self.order.customer, self.customer)
        self.assertEqual(self.order.status, Order.ORDER_STATUS_UNPAID)
        self.assertIsNotNone(self.order.datetime_created)

    def test_order_status_choices(self):
        """Test that status choices are correctly stored."""
        self.order.status = Order.ORDER_STATUS_PAID
        self.order.save()
        self.assertEqual(self.order.status, Order.ORDER_STATUS_PAID)

        self.order.status = Order.ORDER_STATUS_CANCELED
        self.order.save()
        self.assertEqual(self.order.status, Order.ORDER_STATUS_CANCELED)

    def test_order_default_status(self):
        """Test that the default order status is 'unpaid'."""
        new_order = Order.objects.create(customer=self.customer)
        self.assertEqual(new_order.status, Order.ORDER_STATUS_UNPAID)



class OrderItemModelTest(TestCase):

    def setUp(self):
        # Create necessary related objects
        self.user = User.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            password='testpassword123'
        )
        Customer.objects.filter(user=self.user).delete()
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number="123-456-7890"
        )
        self.category = Category.objects.create(name='Office Supplies')
        self.discount = Discount.objects.create(discount=10.0, description="Seasonal Discount")

        self.product = Product.objects.create(
            name='Notebook',
            description='A high-quality notebook.',
            price=Decimal('5.99'),
            category=self.category,
            stock=100
        )
        self.product.discounts.add(self.discount)

        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.ORDER_STATUS_UNPAID
        )

    def test_order_item_creation(self):
        """Test creating an OrderItem and its basic fields."""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=Decimal('5.99')
        )
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, Decimal('5.99'))

    def test_order_item_price_defaults_to_product_price(self):
        """Test that price defaults to product price if not provided."""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3
        )
        self.assertEqual(order_item.price, self.product.price)

    def test_unique_together_constraint(self):
        """Test that an order cannot contain duplicate products."""
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1, price=Decimal('5.99'))

        with self.assertRaises(Exception):  # IntegrityError or Django's built-in catch
            OrderItem.objects.create(order=self.order, product=self.product, quantity=1, price=Decimal('5.99'))

    def test_order_item_str(self):
        """Test the __str__ representation of OrderItem."""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=4,
            price=Decimal('5.99')
        )
        self.assertEqual(str(order_item), '4 x Notebook')



class PaymentModelTest(TestCase):
    
    def setUp(self):
        # Create a user for associating with orders and payments
        self.user = User.objects.create_user(
            email="payuser@example.com",
            username="payuser",
            password="testpass"
        )
        # Create a product with a known price
        self.product = Product.objects.create(
            name="Gadget",
            description="A useful gadget",
            price=Decimal("10.00"),  # Unit price used in cart
            stock=20
        )
        # Create a cart for the user and add an item (2 gadgets => total 20.00)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        # Create an order which auto-calculates total price from cart
        self.order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),  # overridden in save()
            shipping_address="100 Payment Rd"
        )
        # Initialize a Payment linked to the above order
        self.payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price  # should be 20.00 based on cart
        )


    def test_str_returns_order_reference(self):
        # __str__ should include the Order ID
        expected = f"Payment for Order #{self.order.id}"
        self.assertEqual(str(self.payment), expected)


    def test_default_status_pending(self):
        # Newly created payments default to 'pending'
        self.assertEqual(self.payment.status, 'pending')


    def test_complete_payment_marks_status_completed(self):
        # complete_payment() should set status to 'completed' and save the instance
        self.payment.complete_payment()
        # Refresh from DB to ensure save() persisted the change
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')


    def test_fail_payment_marks_status_failed(self):
        # fail_payment() should set status to 'failed'
        self.payment.fail_payment()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')


    def test_payment_date_auto_now_add(self):
        # Test that payment_date was set on creation in setup
        # The timestamp should be between setUp execution and now
        now = timezone.now()
        self.assertLessEqual(self.payment.payment_date, now)
        # And not too far in the past (>= now minus a few seconds)
        self.assertGreaterEqual(self.payment.payment_date, now - timezone.timedelta(seconds=5))


    def test_status_choices_validation(self):
        # Assign an invalid status to a new Payment instance
        bad_payment = Payment(order=self.order, amount=Decimal("0.00"), status="invalid")
        with self.assertRaises(ValidationError):
            bad_payment.full_clean()  # Enforces choices constraint


    def test_one_to_one_constraint_with_order(self):
        # Only one Payment allowed per Order; creating a second should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Payment.objects.create(order=self.order, amount=self.order.total_price)


    def test_deleting_order_cascades_to_payment(self):
        # Deleting the Order should cascade delete the associated Payment created in setup
        self.order.delete()
        with self.assertRaises(Payment.DoesNotExist):
            Payment.objects.get(pk=self.payment.pk)



class CategoryModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="All kinds of electronic items."
        )


    def test_category_creation(self):
        """Test if a Category instance is created correctly."""
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.description, "All kinds of electronic items.")


    def test_string_representation(self):
        """Test the __str__ method of Category."""
        self.assertEqual(str(self.category), "Electronics")


    def test_name_uniqueness(self):
        """Test that the name field must be unique."""
        with self.assertRaises(Exception):  
            Category.objects.create(name="Electronics", description="Duplicate name test")


    def test_description_blank(self):
        """Test that description can be left blank."""
        category = Category.objects.create(name="Books")
        self.assertEqual(category.description, "")  # Should default to blank



class DiscountModelTest(TestCase):

    def setUp(self):
        self.discount = Discount.objects.create(
            discount=10.5,
            description="Spring Sale"
        )

    def test_discount_creation(self):
        """Test if a Discount instance is created correctly."""
        self.assertEqual(self.discount.discount, 10.5)
        self.assertEqual(self.discount.description, "Spring Sale")

    def test_discount_float_field(self):
        """Test if discount field accepts float values correctly."""
        self.discount.discount = 15.75
        self.discount.save()
        self.assertEqual(self.discount.discount, 15.75)

    def test_description_max_length(self):
        """Test if description has a maximum length of 255 characters."""
        max_length = Discount._meta.get_field('description').max_length
        self.assertEqual(max_length, 255)

    def test_string_representation(self):
        """Optionally, if you want to add a __str__ method to Discount, you could test it like this."""
        self.discount.description = "Holiday Discount"
        self.discount.save()



class CustomerModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="testpassword123"
        )

        Customer.objects.filter(user=self.user).delete()

        self.customer = Customer.objects.create(
            user=self.user,
            phone_number="123-456-7890",
            birth_date=date(1990, 5, 20)
        )


    def test_customer_creation(self):
        """Test customer instance is created correctly."""
        self.assertEqual(self.customer.user, self.user)
        self.assertEqual(self.customer.phone_number, "123-456-7890")  # Check the phone number
        self.assertEqual(self.customer.birth_date, date(1990, 5, 20))

    def test_string_representation(self):
        """Test the __str__ method of Customer."""
        self.assertEqual(str(self.customer), "John Doe")

    def test_full_name_property(self):
        """Test the full_name property."""
        self.assertEqual(self.customer.full_name, "John Doe")

    def test_birth_date_can_be_blank(self):
        """Test birth_date can be blank or null."""
        Customer.objects.filter(user=self.user).delete()
        customer_without_birth_date = Customer.objects.create(
            user=self.user,
            phone_number="999-999-9999"
        )
        self.assertIsNone(customer_without_birth_date.birth_date)
