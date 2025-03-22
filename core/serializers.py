from djoser.serializers import UserCreateSerializer

from rest_framework import serializers

from django.contrib.auth import get_user_model



CustomUser = get_user_model()



class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Custom User Registration Serializer with additional validation or fields.
    """
    password = serializers.CharField(write_only=True, required=True)

    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name', 'date_of_birth')

    def validate_password(self, value):
        """
        Custom password validation to ensure password is strong enough.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        """
        Override create method to hash password before saving.
        """
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)  # Hash password before saving
        user.save()
        return user
        