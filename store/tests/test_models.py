from decimal import Decimal
import datetime

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from store.models import Product



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
