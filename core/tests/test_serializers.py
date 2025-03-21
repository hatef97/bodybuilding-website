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



class UserRegistrationSerializerTests(TestCase):

    def setUp(self):
        """Set up test data."""
        self.valid_data = {
            'email': 'valid@example.com',
            'username': 'validuser',
            'password': 'StrongPassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': '1990-01-01'
        }

        self.invalid_data = {
            'email': 'invalid@example.com',
            'username': 'invaliduser',
            'password': 'short',
            'first_name': 'Invalid',
            'last_name': 'User',
            'date_of_birth': '1990-01-01'
        }


    def test_serializer_valid_data(self):
        """Test that serializer is valid with correct data."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())


    def test_serializer_invalid_password(self):
        """Test that serializer raises a validation error for short password."""
        serializer = UserRegistrationSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertEqual(serializer.errors['password'][0], "Password must be at least 8 characters long.")


    def test_serializer_create_user_with_valid_data(self):
        """Test that a user is created with valid data and password is hashed."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        # Save the user using the serializer's create method
        user = serializer.save()

        # Check that user is created in the database
        self.assertEqual(CustomUser.objects.count(), 1)
        created_user = CustomUser.objects.first()

        # Verify that the user fields are correctly set
        self.assertEqual(created_user.email, self.valid_data['email'])
        self.assertEqual(created_user.username, self.valid_data['username'])
        self.assertEqual(created_user.first_name, self.valid_data['first_name'])
        self.assertEqual(created_user.last_name, self.valid_data['last_name'])

        # Check that the password is hashed (not equal to the original plain password)
        self.assertNotEqual(created_user.password, self.valid_data['password'])
        self.assertTrue(created_user.check_password(self.valid_data['password']))


    def test_create_user_without_password(self):
        """Test that serializer raises an error when password is not provided."""
        data = self.valid_data.copy()
        data.pop('password')  # Remove the password

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


    def test_create_user_missing_required_fields(self):
        """Test that serializer raises an error when required fields are missing."""
        data = self.valid_data.copy()
        data.pop('email')  # Remove the email

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)



class UserProfileSerializerTests(TestCase):

    def setUp(self):
        """Create a user for testing the profile serializer."""
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='strongpassword',
            first_name='Test',
            last_name='User',
            date_of_birth='1990-01-01',
            is_active=True
        )
        self.serializer = UserProfileSerializer(instance=self.user)


    def test_serializer_fields(self):
        """Test that the serializer includes the correct fields."""
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth', 'is_active', 'date_joined']))


    def test_serializer_valid_data(self):
        """Test that the serializer is valid with correct data."""
        valid_data = {
            'email': 'updatedemail@example.com',
            'username': 'updatedusername',
            'first_name': 'Updated',
            'last_name': 'User',
            'date_of_birth': '1992-02-02',
            'is_active': False
        }

        serializer = UserProfileSerializer(data=valid_data, instance=self.user)
        self.assertTrue(serializer.is_valid())


    def test_serializer_invalid_data(self):
        """Test that the serializer raises validation errors with invalid data."""
        invalid_data = {
            'email': 'not_an_email',
            'username': '',
            'first_name': 'Updated',
            'last_name': 'User',
            'date_of_birth': 'invalid-date',
            'is_active': 'not_a_boolean'
        }

        serializer = UserProfileSerializer(data=invalid_data, instance=self.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('username', serializer.errors)
        self.assertIn('date_of_birth', serializer.errors)
        self.assertIn('is_active', serializer.errors)


    def test_update_user_profile(self):
        """Test that the update method correctly updates the user profile."""
        updated_data = {
            'first_name': 'UpdatedFirstName',
            'last_name': 'UpdatedLastName',
            'date_of_birth': '1992-02-02',
            'is_active': False
        }

        serializer = UserProfileSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Save the updated data
        updated_user = serializer.save()

        # Verify that the fields were updated
        self.assertEqual(updated_user.first_name, 'UpdatedFirstName')
        self.assertEqual(updated_user.last_name, 'UpdatedLastName')
        self.assertEqual(str(updated_user.date_of_birth), '1992-02-02')
        self.assertFalse(updated_user.is_active)


    def test_update_user_profile_partial(self):
        """Test that the update method allows partial updates."""
        partial_data = {
            'first_name': 'PartialUpdatedFirstName'
        }

        serializer = UserProfileSerializer(instance=self.user, data=partial_data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Save the updated data
        updated_user = serializer.save()

        # Verify that only the first_name field was updated
        self.assertEqual(updated_user.first_name, 'PartialUpdatedFirstName')
        self.assertEqual(updated_user.last_name, 'User')  # last_name remains unchanged
        self.assertEqual(str(updated_user.date_of_birth), '1990-01-01')  # date_of_birth remains unchanged
        self.assertTrue(updated_user.is_active)  # is_active remains unchanged



class ChangePasswordSerializerTests(TestCase):

    def setUp(self):
        """Set up test user for password change."""
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='oldpassword123',  # Set initial password
        )
        self.valid_data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
        }

        self.invalid_data = {
            'old_password': 'wrongoldpassword',
            'new_password': 'short',  # Invalid password (too short)
        }


    def test_serializer_valid_data(self):
        """Test that the serializer is valid with correct old and new passwords."""
        # Initialize the serializer with valid data
        serializer = ChangePasswordSerializer(data=self.valid_data, context={'request': self._mock_request()})
        self.assertTrue(serializer.is_valid())


    def test_serializer_invalid_new_password(self):
        """Test that the serializer raises a validation error for new password being too short."""
        # Set a short new password (less than 8 characters)
        data = self.valid_data.copy()
        data['new_password'] = 'short'  # Invalid new password
        serializer = ChangePasswordSerializer(data=data, context={'request': self._mock_request()})

        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)
        self.assertEqual(serializer.errors['new_password'][0], "New password must be at least 8 characters long.")


    def test_serializer_invalid_old_password(self):
        """Test that the serializer raises a validation error when the old password is incorrect."""
        # Change the old password to a wrong one
        data = self.invalid_data.copy()
        serializer = ChangePasswordSerializer(data=data, context={'request': self._mock_request()})

        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
        self.assertEqual(serializer.errors['old_password'][0], "The old password is incorrect.")


    def test_change_password_successfully(self):
        """Test that the password is successfully changed when the old password is correct."""
        # Create a serializer with valid data
        serializer = ChangePasswordSerializer(data=self.valid_data, context={'request': self._mock_request()})
        self.assertTrue(serializer.is_valid())

        # Call save to change the password
        user = serializer.save()

        # Verify the user’s password has been updated and hashed
        self.assertTrue(user.check_password('newpassword123'))
        self.assertFalse(user.check_password('oldpassword123'))


    def test_missing_new_password(self):
        """Test that the serializer raises an error if new_password is missing."""
        data = {
            'old_password': 'oldpassword123',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': self._mock_request()})

        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)
        self.assertEqual(serializer.errors['new_password'][0], 'This field is required.')


    def test_missing_old_password(self):
        """Test that the serializer raises an error if old_password is missing."""
        data = {
            'new_password': 'newpassword123',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': self._mock_request()})

        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
        self.assertEqual(serializer.errors['old_password'][0], 'This field is required.')


    def _mock_request(self):
        """Helper method to mock request context for the user."""
        class MockRequest:
            def __init__(self, user):
                self.user = user

        return MockRequest(user=self.user)
