from django.test import TestCase

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer

from core.models import *
from core.serializers import *



class CustomUserSerializerTests(TestCase):

    def setUp(self):
        """Create test user."""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': '1990-01-01',
            'is_active': True,
            'is_staff': False
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.serializer = CustomUserSerializer(instance=self.user)



    def test_serializer_creates_valid_user(self):
        """Test that serializer creates a valid user."""
        data = self.serializer.data
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertEqual(data['date_of_birth'], str(self.user.date_of_birth))
        self.assertEqual(data['is_active'], self.user.is_active)
        self.assertEqual(data['is_staff'], self.user.is_staff)


    def test_serializer_with_missing_email(self):
        """Test that serializer raises a validation error when email is missing."""
        data = self.user_data.copy()
        data.pop('email')  
        data['username'] = 'uniqueusername'

        serializer = CustomUserSerializer(data=data)

        serializer.is_valid()

        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0].code, 'required')
        self.assertEqual(str(serializer.errors['email'][0]), 'This field is required.')



    def test_serializer_with_missing_username(self):
        """Test that serializer raises a validation error when username is missing."""
        data = self.user_data.copy()
        data.pop('username')  

        data['email'] = 'uniqueemail@example.com'  

        serializer = CustomUserSerializer(data=data)

        serializer.is_valid()

        self.assertIn('username', serializer.errors)
        self.assertEqual(serializer.errors['username'][0].code, 'required')
        self.assertEqual(str(serializer.errors['username'][0]), 'This field is required.')



    def test_serializer_update_user(self):
        """Test that serializer correctly updates a user's fields."""
        updated_data = {
            'first_name': 'UpdatedName',
            'last_name': 'UpdatedLastName'
        }
        serializer = CustomUserSerializer(self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'UpdatedName')
        self.assertEqual(updated_user.last_name, 'UpdatedLastName')



    def test_serializer_invalid_date_of_birth(self):
        """Test that serializer raises a validation error with invalid date format."""
        invalid_data = {
            'email': 'valid@example.com',
            'username': 'validuser',
            'first_name': 'Valid',
            'last_name': 'User',
            'date_of_birth': 'invalid-date',  # Invalid date format
            'is_active': True,
            'is_staff': False
        }

        serializer = CustomUserSerializer(data=invalid_data)

        serializer.is_valid()

        self.assertIn('date_of_birth', serializer.errors)
        self.assertEqual(serializer.errors['date_of_birth'][0].code, 'invalid')
        self.assertEqual(str(serializer.errors['date_of_birth'][0]), 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.')



    def test_serializer_valid_data(self):
        """Test serializer with valid data and ensure it passes validation."""
        valid_data = {
            'email': 'valid@example.com',
            'username': 'validuser',
            'first_name': 'Valid',
            'last_name': 'User',
            'date_of_birth': '2000-01-01',
            'is_active': True,
            'is_staff': False
        }
        serializer = CustomUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, valid_data['email'])
        self.assertEqual(user.username, valid_data['username'])
        self.assertEqual(user.first_name, valid_data['first_name'])
        self.assertEqual(user.last_name, valid_data['last_name'])
        self.assertEqual(str(user.date_of_birth), valid_data['date_of_birth'])
