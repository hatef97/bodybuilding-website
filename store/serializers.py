from rest_framework import serializers

from .models import Product, Cart, CartItem, Order, Payment
from core.models import CustomUser as User



class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model, exposing all relevant fields and computed stock status.
    Includes validation to ensure price and stock integrity.
    """
    # Include a read-only field for stock availability
    is_in_stock = serializers.BooleanField(read_only=True)
    # Use URL for image representation; allow null/blank
    image_url = serializers.ImageField(source='image', use_url=True, required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        model = Product
        # Include all fields plus computed is_in_stock and image_url
        fields = [
            'id',
            'name',
            'description',
            'price',
            'stock',
            'is_in_stock',
            'image_url',
            'created_at',
        ]
        # created_at and is_in_stock should be read-only
        read_only_fields = ('id', 'is_in_stock', 'created_at')

    def validate_price(self, value):
        """
        Ensure the product price is non-negative and has at most two decimal places.
        """
        if value < 0:
            raise serializers.ValidationError("Price must be a non-negative value.")
        return round(value, 2)

    def validate_stock(self, value):
        """
        Ensure stock is an integer >= 0.
        """
        if value < 0:
            raise serializers.ValidationError("Stock must be zero or a positive integer.")
        return value

    def create(self, validated_data):
        """
        Override create to handle any custom logic (e.g., setting defaults) before saving.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Override update to allow partial updates and maintain business rules.
        """
        return super().update(instance, validated_data)



class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem, nested under Cart. Supports read/write of product and quantity.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    total_price = serializers.DecimalField(
        source='total_price', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ('id', 'product', 'total_price')



class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model, including nested items and total calculation.
    """
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), default=serializers.CurrentUserDefault()
    )
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    total_price = serializers.DecimalField(
        source='total_price', max_digits=10, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at']
        read_only_fields = ('id', 'total_price', 'created_at')

    def create(self, validated_data):
        """
        Create a new Cart instance tied to the user.
        """
        return Cart.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update Cart metadata only; manipulation of items should use dedicated endpoints.
        """
        return super().update(instance, validated_data)



class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model. Reads from cart and exposes nested items.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    status = serializers.ChoiceField(choices=Order.ORDER_STATUS_CHOICES, default='pending')
    items = CartItemSerializer(source='cart.cart_items', many=True, read_only=True)
    total_price = serializers.DecimalField(
        source='total_price', max_digits=10, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'items', 'total_price', 'shipping_address', 'created_at']
        read_only_fields = ('id', 'user', 'items', 'total_price', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        cart = validated_data.pop('cart', None)
        return Order.objects.create(user=user, cart=cart, **validated_data)

    def update(self, instance, validated_data):
        # Allow status and shipping_address updates only
        instance.status = validated_data.get('status', instance.status)
        instance.shipping_address = validated_data.get('shipping_address', instance.shipping_address)
        instance.save()
        return instance



# New serializer for Payment model
class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model, exposing status control and order relation.
    Includes methods to complete or fail payments through API updates.
    """
    user = serializers.ReadOnlyField(source='order.user.username')
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source='order'
    )
    payment_date = serializers.DateTimeField(read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.ChoiceField(
        choices=Payment.PAYMENT_STATUS_CHOICES, default='pending'
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'order_id', 'user', 'payment_date', 'amount', 'status'
        ]
        read_only_fields = ('id', 'user', 'payment_date')

    def validate_amount(self, value):
        """
        Ensure amount is non-negative and matches the related order total.
        """
        if value < 0:
            raise serializers.ValidationError("Payment amount must be non-negative.")
        # Optional: enforce matching order total
        order = self.initial_data.get('order_id') or self.instance.order
        try:
            order_obj = Order.objects.get(pk=order) if not hasattr(order, 'total_price') else order
            if value != order_obj.total_price:
                raise serializers.ValidationError("Payment amount must equal order total.")
        except Order.DoesNotExist:
            pass
        return round(value, 2)

    def create(self, validated_data):
        """
        Create a new Payment instance. Sets status after creation if needed.
        """
        payment = super().create(validated_data)
        if payment.status == 'completed':
            payment.complete_payment()
        elif payment.status == 'failed':
            payment.fail_payment()
        return payment

    def update(self, instance, validated_data):
        """
        Update status via complete_payment or fail_payment methods
        """
        new_status = validated_data.get('status')
        if new_status and new_status != instance.status:
            if new_status == 'completed':
                instance.complete_payment()
            elif new_status == 'failed':
                instance.fail_payment()
        return instance
