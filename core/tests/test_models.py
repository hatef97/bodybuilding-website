from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError



class CustomUserManagerTests(TestCase):

    def setUp(self):
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
