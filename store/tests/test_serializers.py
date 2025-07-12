from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import ValidationError

from store.models import Product
from store.serializers import ProductSerializer



class ProductSerializerTests(APITestCase):
    """
    APITestCase suite for the ProductSerializer, covering field inclusion,
    computed fields, validation, rounding, and create/update behavior.
    """

    def setUp(self):
        # Prepare request context for URL fields
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')

        # Create a base product instance for update tests
        self.product = Product.objects.create(
            name="Sample Product",
            description="Initial description",
            price=9.99,
            stock=10
        )

        # Payload for valid create/update
        self.valid_data = {
            "name": "New Product",
            "description": "Test creation",
            "price": 15.755,
            "stock": 5
        }


    def test_fields_present(self):
        """
        Serializer output includes exactly the declared fields.
        """
        serializer = ProductSerializer(self.product, context={'request': self.request})
        data_keys = set(serializer.data.keys())
        expected = {"id", "name", "description", "price", "stock", "is_in_stock", "image_url", "created_at"}
        self.assertSetEqual(data_keys, expected)


    def test_is_in_stock_flag(self):
        """
        Computed is_in_stock is False at zero stock, True otherwise.
        """
        # Zero stock → False
        self.product.stock = 0
        self.product.save()
        serializer = ProductSerializer(self.product, context={'request': self.request})
        self.assertFalse(serializer.data['is_in_stock'])

        # Positive stock → True
        self.product.stock = 3
        self.product.save()
        serializer = ProductSerializer(self.product, context={'request': self.request})
        self.assertTrue(serializer.data['is_in_stock'])


    def test_image_url_handling(self):
        """
        image_url is None without an image, and returns a URL when image is set.
        """
        # No image
        serializer = ProductSerializer(self.product, context={'request': self.request})
        self.assertIsNone(serializer.data['image_url'])

        # Attach an image
        img = SimpleUploadedFile('test.png', b'\x89PNG\r\n', content_type='image/png')
        self.product.image = img
        self.product.save()
        serializer = ProductSerializer(self.product, context={'request': self.request})
        url = serializer.data['image_url']
        self.assertTrue(url.endswith('test.png'))


    def test_validate_price_negative(self):
        """
        Negative price should trigger a ValidationError.
        """
        data = self.valid_data.copy()
        data['price'] = -0.01
        serializer = ProductSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_validate_price_rounding(self):
        """
        Price is rounded to two decimal places on validation.
        """
        data = self.valid_data.copy()
        data['price'] = 2.129
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.price, Decimal('2.13'))


    def test_validate_stock_negative(self):
        """
        Negative stock should trigger a ValidationError.
        """
        data = self.valid_data.copy()
        data['stock'] = -5
        serializer = ProductSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_create_product(self):
        """
        Saving a valid serializer should create a new Product instance.
        """
        serializer = ProductSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        new_product = serializer.save()
        self.assertIsInstance(new_product, Product)
        self.assertEqual(new_product.name, self.valid_data['name'])
        self.assertEqual(new_product.stock, self.valid_data['stock'])
        self.assertEqual(new_product.price, Decimal(str(round(self.valid_data['price'], 2))))


    def test_update_product_partial(self):
        """
        Partial update should only change the provided fields.
        """
        update_data = {"name": "Updated Product", "stock": 20}
        serializer = ProductSerializer(self.product, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.name, update_data['name'])
        self.assertEqual(updated.stock, update_data['stock'])
        # Other fields remain unchanged
        self.assertEqual(updated.price, self.product.price)
        self.assertEqual(updated.description, self.product.description)
