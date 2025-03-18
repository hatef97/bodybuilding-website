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
        