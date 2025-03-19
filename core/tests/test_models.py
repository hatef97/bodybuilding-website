from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import CustomUser



class CustomUserManagerTests(TestCase):
    
    def setUp(self):
        """Set up the test data for each test."""
        self.User = get_user_model()
        self.user_manager = self.User.objects


    def test_create_user_with_valid_email(self):
        # Verifies user creation with a valid email and password, ensuring default attributes are False.
        user = self.user_manager.create_user(email="test@example.com", password="securepassword")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("securepassword"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


    def test_create_user_without_email_raises_error(self):
        # Ensures a ValueError is raised when email is missing.
        with self.assertRaises(ValueError) as context:
            self.user_manager.create_user(email=None, password="password")
        self.assertEqual(str(context.exception), "The Email field must be set")


    def test_create_superuser_with_valid_email(self):
        # Confirms superuser creation with valid email and password, checking attributes are correct.
        superuser = self.user_manager.create_superuser(email="admin@example.com", password="adminpassword")
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.check_password("adminpassword"))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


    def test_create_superuser_defaults_to_is_staff_and_is_superuser(self):
        # Ensures superuser defaults is_staff and is_superuser to True.
        superuser = self.user_manager.create_superuser(email="admin@example.com", password="adminpassword")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


    def test_create_superuser_with_is_staff_false_raises_error(self):
        # Verifies error is raised when is_staff is False for a superuser.
        with self.assertRaises(ValueError):
            self.user_manager.create_superuser(email="admin@example.com", password="adminpassword", is_staff=False)


    def test_create_superuser_with_is_superuser_false_raises_error(self):
        # Ensures error is raised if is_superuser is False for a superuser.
        with self.assertRaises(ValueError):
            self.user_manager.create_superuser(email="admin@example.com", password="adminpassword", is_superuser=False)



class CustomUserModelTests(TestCase):

    def setUp(self):
        """Set up the test data for each test."""
        self.email = 'test@example.com'
        self.username = 'testuser'
        self.password = 'password'
        self.superuser_email = 'admin@example.com'
        self.superuser_username = 'admin'
        self.superuser_password = 'adminpassword'
        
        # Creating a regular user
        self.user = CustomUser.objects.create_user(
            email=self.email,
            username=self.username,
            password=self.password
        )

        # Creating a superuser
        self.superuser = CustomUser.objects.create_superuser(
            email=self.superuser_email,
            username=self.superuser_username,
            password=self.superuser_password
        )


    def test_create_user_with_email_and_username(self):
        """Ensure a user is created with email and username."""
        self.assertEqual(self.user.email, self.email)
        self.assertEqual(self.user.username, self.username)
        self.assertTrue(self.user.check_password(self.password))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)


    def test_create_superuser(self):
        """Ensure a superuser is created with is_staff and is_superuser as True."""
        self.assertEqual(self.superuser.email, self.superuser_email)
        self.assertEqual(self.superuser.username, self.superuser_username)
        self.assertTrue(self.superuser.check_password(self.superuser_password))
        self.assertTrue(self.superuser.is_active)
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_staff)


    def test_create_user_without_email(self):
        """Ensure that a ValueError is raised when no email is provided."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', username='user', password=self.password)


    def test_create_user_without_username(self):
        """Ensure that a ValueError is raised when no username is provided."""
        with self.assertRaises(ValidationError):
            user = CustomUser.objects.create_user(
                email='user@example.com',
                username='',  # Empty username
                password=self.password
            )
            user.full_clean()

    def test_user_string_representation(self):
        """Test the string representation of the user."""
        self.assertEqual(str(self.user), self.email)


    def test_date_joined_is_auto_set(self):
        """Ensure that the date_joined field is automatically set to the current date/time."""
        self.assertTrue(self.user.date_joined <= self.superuser.date_joined)


    def test_user_fields_optional(self):
        """Test that first_name, last_name, and date_of_birth are optional."""
        self.assertIsNone(self.user.first_name)
        self.assertIsNone(self.user.last_name)
        self.assertIsNone(self.user.date_of_birth)


    def test_user_is_active_default(self):
        """Ensure that a user is active by default."""
        self.assertTrue(self.user.is_active)


    def test_is_superuser_false_by_default(self):
        """Ensure that the is_superuser field is False by default."""
        self.assertFalse(self.user.is_superuser)


    def test_is_staff_false_by_default(self):
        """Ensure that the is_staff field is False by default."""
        self.assertFalse(self.user.is_staff)
