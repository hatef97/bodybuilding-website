from decimal import Decimal
import datetime

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from store.models import Product, Cart, CartItem
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
