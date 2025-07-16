from decimal import Decimal
import datetime

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from store.models import *
from core.models import CustomUser as User



class ProductModelTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="A product for testing",
            price=Decimal("19.99"),
            stock=10,
            image=None,
        )


    def test_str_representation(self):
        self.assertEqual(str(self.product), "Test Product")


    def test_product_fields(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.description, "A product for testing")
        self.assertEqual(self.product.price, Decimal("19.99"))
        self.assertEqual(self.product.stock, 10)
        self.assertIsNone(self.product.image.name)
        self.assertIsInstance(self.product.created_at, datetime.datetime)


    def test_is_in_stock_true(self):
        self.assertTrue(self.product.is_in_stock())


    def test_is_in_stock_false(self):
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_in_stock())


    def test_decrease_stock_success(self):
        result = self.product.decrease_stock(5)
        self.assertTrue(result)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)


    def test_decrease_stock_failure(self):
        result = self.product.decrease_stock(15)
        self.assertFalse(result)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)


    def test_increase_stock(self):
        self.product.increase_stock(7)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 17)


    def test_optional_image_upload(self):
        image_file = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        product_with_image = Product.objects.create(
            name="Image Product",
            description="Has image",
            price=Decimal("29.99"),
            stock=3,
            image=image_file
        )
        self.assertIsNotNone(product_with_image.image)
        self.assertIn("products/test_image.jpg", product_with_image.image.name)



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
        # Create a test user to associate with Order
        self.user = User.objects.create_user(
            email="orderuser@example.com",
            username="orderuser",
            password="securepass"
        )
        # Create a product with a fixed price for predictable calculations
        self.product = Product.objects.create(
            name="Widget",
            description="A handy widget",
            price=Decimal("5.00"),  # Unit price
            stock=50
        )
        # Create a cart tied to our test user
        self.cart = Cart.objects.create(user=self.user)
        # Add an item to the cart: 2 widgets at 5.00 each => total 10.00
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)


    def test_str_returns_order_id_and_user(self):
        # Order.__str__ should output "Order #<id> by <user>"
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),  # Dummy, overridden in save()
            shipping_address="123 Test Lane"
        )
        expected = f"Order #{order.id} by {self.user}"
        self.assertEqual(str(order), expected)


    def test_save_sets_total_price_from_cart(self):
        # Instantiate with incorrect total_price, then save should recalc
        order = Order(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("999.99"),  # Will be overridden
            shipping_address="456 Sample Road"
        )
        order.save()  # triggers recalculation
        # Expected total is cart.total_price(): 5.00 * 2 = 10.00
        self.assertEqual(order.total_price, self.cart.total_price())


    def test_default_status_pending(self):
        # Creating without specifying status defaults to 'pending'
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),
            shipping_address="789 Example Blvd"
        )
        self.assertEqual(order.status, 'pending')


    def test_status_choices_validation(self):
        # Assign an invalid status and expect a validation error
        order = Order(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),
            shipping_address="1010 Error St",
            status="invalid_status"
        )
        with self.assertRaises(ValidationError):
            order.full_clean()  # checks choices constraint


    def test_created_at_auto_now_add(self):
        # Record time before creation
        before = timezone.now()
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),
            shipping_address="1111 Time Ave"
        )
        # created_at should be set on save() and be >= before
        self.assertGreaterEqual(order.created_at, before)
        # And not in the future (<= now)
        self.assertLessEqual(order.created_at, timezone.now())


    def test_cart_one_to_one_constraint(self):
        # Only one Order per Cart; second creation should error
        Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),
            shipping_address="2222 Single Rd"
        )
        with self.assertRaises(IntegrityError):
            Order.objects.create(
                user=self.user,
                cart=self.cart,
                total_price=Decimal("0.00"),
                shipping_address="3333 Duplicate Dr"
            )


    def test_deleting_cart_cascades_to_order(self):
        # Deleting the cart should cascade delete the linked Order
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            total_price=Decimal("0.00"),
            shipping_address="4444 Cascade Ct"
        )
        # Remove the cart
        self.cart.delete()
        # Order should be removed from the DB
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(pk=order.pk)



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
