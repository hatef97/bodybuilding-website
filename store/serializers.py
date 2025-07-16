from rest_framework import serializers

from django.utils.text import slugify
from django.db import transaction

from .models import *
from core.models import CustomUser as User



class CategorySerializer(serializers.ModelSerializer):
    num_of_products = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ["id", "name", "description", "num_of_products"]

    def validate(self, data):
        if len(data['name']) < 3:
            raise serializers.ValidationError('Category title should be at least 3.')
        return data



class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price",
                  "category", "category_name", "stock",
                  "image", "created_at"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value
    
    def create(self, validated_data):
          product = Product(**validated_data)
          product.slug = slugify(product.name)
          product.save()
          return product



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'id',
            'name',
            'body',
        ]
        
    def create(self, validated_data):
        product_id = self.context['product_pk']    
        return Comment.objects.create(product_id=product_id, **validated_data)



class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone_number', 'birth_date']      
        read_only_fields = ['user']



class CartProductSeializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            ]



class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

    def create(self, validated_data):
        cart_id = self.context['cart_pk']

        product = validated_data.get('product')
        quantity = validated_data.get('quantity')

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product.id)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id, **validated_data)

        self.instance = cart_item
        return cart_item



class UpadateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']



class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model, including nested items and total calculation.
    """
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), default=serializers.CurrentUserDefault()
    )
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
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
        max_digits=10, decimal_places=2, read_only=True
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
