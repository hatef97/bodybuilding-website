from djoser.serializers import UserCreateSerializer, UserSerializer, PasswordChangeSerializer

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



class CustomPasswordChangeSerializer(PasswordChangeSerializer):
    """
    Custom Password Change Serializer with additional validation.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        """
        Custom validation for the new password (e.g., length requirement).
        """
        if len(value) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")
        return value

    def validate_old_password(self, value):
        """
        Validate the old password. You can add further logic here (e.g., check if password matches).
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("The old password is incorrect.")
        return value

    def save(self):
        """
        Change the password for the user.
        """
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
        