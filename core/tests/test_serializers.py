from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from core.serializers import CustomUserCreateSerializer, CustomUserProfileSerializer
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



class CustomUserProfileSerializerTests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="user1",
            password="testpass123",
            first_name="Old",
            last_name="Name",
            date_of_birth="1990-01-01"
        )


    def test_profile_update_successful(self):
        """Test that user profile is updated successfully."""
        updated_data = {
            "first_name": "New",
            "last_name": "Name",
            "date_of_birth": "1995-05-05",
            "is_active": False  # intentionally changing active status
        }
        serializer = CustomUserProfileSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, "New")
        self.assertEqual(updated_user.last_name, "Name")
        self.assertEqual(str(updated_user.date_of_birth), "1995-05-05")
        self.assertFalse(updated_user.is_active)


    def test_read_only_fields_are_not_updated(self):
        """Test that read-only fields like email/username are not changed."""
        updated_data = {
            "email": "hacked@example.com",
            "username": "hacker",
            "first_name": "Still",
            "last_name": "Safe"
        }
        serializer = CustomUserProfileSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        # Read-only fields should remain unchanged
        self.assertEqual(updated_user.email, self.user.email)
        self.assertEqual(updated_user.username, self.user.username)


    def test_invalid_date_of_birth_format(self):
        """Test that invalid date format raises validation error."""
        invalid_data = {
            "date_of_birth": "invalid-date"
        }
        serializer = CustomUserProfileSerializer(instance=self.user, data=invalid_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_of_birth", serializer.errors)
