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
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name', 'date_of_birth')


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



class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profile details.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth', 'is_active', 'date_joined')
        read_only_fields = ('id', 'email', 'username', 'date_joined')


    def update(self, instance, validated_data):
        """
        Update the user profile with the new data.
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance



class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing the user's password.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, required=True)


    def validate_new_password(self, value):
        """
        Custom validation for the new password (e.g., length requirement).
        """
        if len(value) < 8:
            raise ValidationError("New password must be at least 8 characters long.")
        return value


    def validate_old_password(self, value):
        """
        Validate the old password. You can add further logic here (e.g., check if password matches).
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("The old password is incorrect.")
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
