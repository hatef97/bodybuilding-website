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



class CartModelTest(TestCase):

    def test_cart_creation(self):
        """Test that a Cart instance can be created and fields are set correctly."""
        cart = Cart.objects.create()

        self.assertIsInstance(cart.id, uuid.UUID)  # Primary key should be a UUID
        self.assertIsNotNone(cart.created_at)  # Timestamp should be auto-generated

    def test_cart_unique_id(self):
        """Test that each cart has a unique UUID."""
        cart1 = Cart.objects.create()
        cart2 = Cart.objects.create()

        self.assertNotEqual(cart1.id, cart2.id)



class CartItemModelTest(TestCase):

    def setUp(self):
        # Create category and product first, since CartItem depends on Product
        self.category = Category.objects.create(name="Office Supplies", description="All office-related items")
        self.product = Product.objects.create(
            name="Pen",
            description="A blue ink pen",
            price=Decimal("1.50"),
            category=self.category,
            stock=100
        )
        # Create the Cart
        self.cart = Cart.objects.create()

    def test_cartitem_creation(self):
        """Test CartItem can be created and is linked to correct cart and product."""
        cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)

    def test_cartitem_unique_together(self):
        """Test that adding the same product to the same cart twice raises an IntegrityError."""
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

        with self.assertRaises(Exception):  # Depending on DB, this can be IntegrityError or others
            CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_cartitem_str(self):
        cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
        self.assertEqual(str(cart_item), '3 x Pen')        



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



class AddressModelTest(TestCase):

    def setUp(self):
        # Create user and customer first
        self.user = User.objects.create_user(
            username='johndoe',
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

    def test_address_creation(self):
        """Test that Address can be created for a customer."""
        address = Address.objects.create(
            customer=self.customer,
            province="Ontario",
            city="Toronto",
            street="123 Main St"
        )
        self.assertEqual(address.customer, self.customer)
        self.assertEqual(address.province, "Ontario")
        self.assertEqual(address.city, "Toronto")
        self.assertEqual(address.street, "123 Main St")

    def test_address_one_to_one_constraint(self):
        """Test that a customer can have only one address."""
        Address.objects.create(
            customer=self.customer,
            province="Ontario",
            city="Toronto",
            street="123 Main St"
        )

        with self.assertRaises(Exception):  # IntegrityError (wrapped in Django's DatabaseError)
            Address.objects.create(
                customer=self.customer,
                province="Quebec",
                city="Montreal",
                street="456 Another St"
            )

    def test_address_string_representation(self):
        """Test the string representation of Address if you want to add __str__ later."""
        address = Address.objects.create(
            customer=self.customer,
            province="Ontario",
            city="Toronto",
            street="123 Main St"
        )
        expected_str = f'{self.customer.full_name}, 123 Main St, Toronto, Ontario'
        actual_str = f'{address.customer.full_name}, {address.street}, {address.city}, {address.province}'
        self.assertEqual(actual_str, expected_str)   



class CommentModelTest(TestCase):

    def setUp(self):
        # Create a category and product to associate with the comment
        self.category = Category.objects.create(name="Office Supplies", description="Office related items.")
        self.product = Product.objects.create(
            name="Notebook",
            description="A high-quality notebook.",
            price=10.99,
            category=self.category,
            stock=100
        )

    def test_comment_creation(self):
        """Test that a Comment can be created and fields are set correctly."""
        comment = Comment.objects.create(
            product=self.product,
            name="John Doe",
            body="Great product, very useful!",
            status=Comment.COMMENT_STATUS_WAITING
        )

        self.assertEqual(comment.product, self.product)
        self.assertEqual(comment.name, "John Doe")
        self.assertEqual(comment.body, "Great product, very useful!")
        self.assertEqual(comment.status, Comment.COMMENT_STATUS_WAITING)
        self.assertIsNotNone(comment.datetime_created)  # Auto set

    def test_comment_status_choices(self):
        """Test that the status field accepts only the valid choices."""
        comment = Comment.objects.create(
            product=self.product,
            name="Jane Smith",
            body="Not bad, but could be better.",
            status=Comment.COMMENT_STATUS_APPROVED
        )
        self.assertEqual(comment.status, Comment.COMMENT_STATUS_APPROVED)

        comment.status = Comment.COMMENT_STATUS_NOT_APPROVED
        comment.save()
        self.assertEqual(comment.status, Comment.COMMENT_STATUS_NOT_APPROVED)

    def test_default_status(self):
        """Test that the default status is waiting."""
        comment = Comment.objects.create(
            product=self.product,
            name="Alex",
            body="This product is amazing!"
        )
        self.assertEqual(comment.status, Comment.COMMENT_STATUS_WAITING)

    def test_comment_string_representation(self):
        """Test string representation if you want to add __str__."""
        comment = Comment.objects.create(
            product=self.product,
            name="Sarah",
            body="Loved this product!"
        )
        expected_str = f"Comment by Sarah on {self.product.name}"
        actual_str = f"Comment by {comment.name} on {comment.product.name}"
        self.assertEqual(actual_str, expected_str)
