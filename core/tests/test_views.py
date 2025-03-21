from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.urls import reverse



CustomUser = get_user_model()



class UserRegistrationViewSetTests(APITestCase):

    def setUp(self):
        """Set up test users and URLs."""
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='adminuser',
            password='adminpassword',
            is_staff=True
        )
        self.regular_user = CustomUser.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='testpassword'
        )

        # Obtain authentication tokens for users
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.user_token = Token.objects.create(user=self.regular_user)

        self.registration_url = reverse('user-registration-list')


    def test_admin_can_list_users(self):
        """Test that an admin user can list all users."""
        self.client.force_authenticate(user=self.admin_user) 
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        response = self.client.get(self.registration_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data[0])  # Checking if user data is returned


    def test_non_admin_cannot_list_users(self):
        """Test that a non-admin user cannot list users."""
        self.client.force_authenticate(user=self.regular_user)  # Authenticate as regular user
        response = self.client.get(self.registration_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  
        self.assertEqual(response.data['detail'], "You do not have permission to perform this action.")  
    

    def test_unauthenticated_user_cannot_list_users(self):
        """Test that an unauthenticated user cannot list users."""
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  


    def test_successful_user_registration(self):
        """Test that a new user can be registered successfully."""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newuserpassword',
            'first_name': 'New',
            'last_name': 'User',
            'date_of_birth': '1995-05-05'
        }

        response = self.client.post(self.registration_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['username'], data['username'])

        # Ensure the user is actually created in the database
        self.assertTrue(CustomUser.objects.filter(email=data['email']).exists())


    def test_registration_fails_with_invalid_data(self):
        """Test that registration fails when provided invalid data."""
        data = {
            'email': 'invalid-email',
            'username': '',  # Username is required
            'password': 'short',  # Password too short (assuming password validation)
            'first_name': 'User',
            'last_name': 'Test',
            'date_of_birth': 'invalid-date'  # Invalid date format
        }

        response = self.client.post(self.registration_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)
        self.assertIn('date_of_birth', response.data)


    def test_registration_fails_with_existing_email(self):
        """Test that registration fails if the email is already used."""
        data = {
            'email': self.regular_user.email,  # Duplicate email
            'username': 'anotheruser',
            'password': 'anotherpassword',
            'first_name': 'Another',
            'last_name': 'User',
            'date_of_birth': '1998-03-03'
        }

        response = self.client.post(self.registration_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)  # Should return an email already exists error


    def test_registration_fails_with_existing_username(self):
        """Test that registration fails if the username is already taken."""
        data = {
            'email': 'uniqueemail@example.com',
            'username': self.regular_user.username,  # Duplicate username
            'password': 'validpassword',
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': '2000-01-01'
        }

        response = self.client.post(self.registration_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)  # Should return a username already exists error



class UserProfileViewSetTests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="testuser",
            password="testpassword",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Assume your profile detail endpoint looks like this:
        self.profile_url = reverse('user-profile-detail', kwargs={'pk': self.user.pk})


    def test_retrieve_user_profile(self):
        """Test that a user can retrieve their own profile."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)


    def test_update_user_profile(self):
        """Test that a user can update their own profile."""
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1995-05-05",
            "is_active": False  # Field in serializer
        }
        response = self.client.put(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fetch the user again from DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data['first_name'])
        self.assertEqual(self.user.last_name, update_data['last_name'])
        self.assertEqual(str(self.user.date_of_birth), update_data['date_of_birth'])
        self.assertFalse(self.user.is_active)


    def test_unauthenticated_user_cannot_access_profile(self):
        """Test that unauthenticated users cannot access profile endpoints."""
        self.client.force_authenticate(user=None)  # Logout
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_partial_update_user_profile(self):
        """Test that a user can partially update their profile."""
        partial_data = {"first_name": "Updated"}
        response = self.client.patch(self.profile_url, partial_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Doe")  # unchanged


    def test_user_cannot_access_another_users_profile(self):
        """Test that users cannot access or update other users' profiles."""
        other_user = CustomUser.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="otherpassword"
        )
        other_user_url = reverse('user-profile-detail', kwargs={'pk': other_user.pk})

        response = self.client.get(other_user_url)
        # Since get_object returns request.user, this shouldn't return the other user
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
