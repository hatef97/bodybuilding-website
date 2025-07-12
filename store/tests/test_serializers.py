from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import ValidationError

from store.models import Product, Cart, CartItem, Order
from store.serializers import ProductSerializer, CartItemSerializer, CartSerializer, OrderSerializer
from core.models import CustomUser as User



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
