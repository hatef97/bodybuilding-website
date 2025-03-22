from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from core.serializers import CustomUserCreateSerializer
from core.models import CustomUser



class CustomUserCreateSerializerTests(APITestCase):
    def setUp(self):
        self.valid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "strongpass123",
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1990-01-01"
        }


    def test_valid_user_registration(self):
        """Test serializer with valid user data creates user successfully."""
        serializer = CustomUserCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertTrue(user.check_password(self.valid_data["password"]))


    def test_missing_required_fields(self):
        """Test serializer fails when required fields are missing."""
        invalid_data = self.valid_data.copy()
        invalid_data.pop("email")
        serializer = CustomUserCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


    def test_password_too_short(self):
        """Test password validation fails when password is too short."""
        data = self.valid_data.copy()
        data["password"] = "123"
        serializer = CustomUserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "Password must be at least 8 characters long.")
