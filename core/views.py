from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import *



class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    serializer_class = UserRegistrationSerializer
    