from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import *



class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    serializer_class = UserRegistrationSerializer



class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for viewing and updating user profile details.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



class ChangePasswordView(generics.UpdateAPIView):
    """
    API view for changing the user's password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
        