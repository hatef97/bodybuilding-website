from rest_framework import generics, viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .serializers import *



class UserRegistrationViewSet(viewsets.GenericViewSet):
    """
    API view for user registration.
    """
    serializer_class = UserRegistrationSerializer
    # Define the queryset to retrieve users
    queryset = CustomUser.objects.all()

    def get_permissions(self):
        """
        Allow anyone to register but restrict listing users to admins.
        """
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]


    def create(self, request, *args, **kwargs):
        """
        Handle user registration (POST).
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()  # Save the new user to the database
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        """
        List all users - only accessible by admin.
        """
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        # Use the queryset to retrieve the list of users
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class UserProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    API view for viewing and updating user profile details.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # This will allow each user to access their own profile
        return self.request.user

    @action(detail=False, methods=["get", "put"], url_path="me")
    def me(self, request):
        if request.method == "GET":
            serializer = self.get_serializer(self.request.user)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = self.get_serializer(self.request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)



class ChangePasswordViewSet(viewsets.GenericViewSet):
    """
    API view for changing the user's password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]


    def get_object(self):
        return self.request.user


    def update(self, request, *args, **kwargs):
        """
        Handle password change.
        """
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."})
        return Response(serializer.errors, status=400)
