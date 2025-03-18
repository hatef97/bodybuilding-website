from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError



# Use the CustomUser model if it's defined
CustomUser = get_user_model()



class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer to handle custom user details.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth', 'is_active', 'is_staff', 'date_joined')



class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user. It handles password hashing.
    """
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'date_of_birth')


    def validate_password(self, value):
        """
        Custom password validation to ensure password is strong enough.
        """
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return value


    def create(self, validated_data):
        """
        Create a new user with hashed password.
        """
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)  # Hash the password before saving
        user.save()
        return user
