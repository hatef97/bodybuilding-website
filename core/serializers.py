from djoser.serializers import UserCreateSerializer, UserSerializer

from rest_framework import serializers

from django.contrib.auth import get_user_model



CustomUser = get_user_model()



class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Custom User Registration Serializer with additional validation.
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



class CustomUserProfileSerializer(UserSerializer):
    """
    Custom User Profile Serializer for handling user details (view and update).
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth', 'is_active', 'is_staff', 'date_joined')
        read_only_fields = ('id', 'email', 'username', 'date_joined')

    def update(self, instance, validated_data):
        """
        Override update method to update the user profile.
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance
