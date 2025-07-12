from rest_framework import serializers

from .models import Product



class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model, exposing all relevant fields and computed stock status.
    Includes validation to ensure price and stock integrity.
    """
    # Include a read-only field for stock availability
    is_in_stock = serializers.BooleanField(source='is_in_stock', read_only=True)
    # Use URL for image representation; allow null/blank
    image_url = serializers.ImageField(source='image', use_url=True, required=False, allow_null=True)

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
