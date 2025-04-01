from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from core.models import CustomUser as User



class TestURLs(APITestCase):

    def setUp(self):
            """Set up user with email and authentication."""
            # Create a user with an email, username, and password
            self.user = User.objects.create_user(
                email='user@mail.com',  # Email should be provided
                username='user',
                password='password'
            )
            # Force authenticate the client with the created user
            self.client.force_authenticate(user=self.user)


    def test_meal_url(self):
        """Test the meal URL."""
        url = reverse('meal-list')  # URL for listing meals (viewset)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_mealplan_url(self):
        """Test the mealplan URL."""
        url = reverse('mealplan-list')  # URL for listing meal plans (viewset)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_recipe_url(self):
        """Test the recipe URL."""
        url = reverse('recipe-list')  # URL for listing recipes (viewset)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_calorie_calculator_url(self):
        """Test the calorie calculator URL."""
        url = reverse('caloriecalculator-list')  # URL for listing calorie calculators (viewset)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_calculate_calories_url(self):
        """Test the custom calculate_calories action URL."""
        url = reverse('caloriecalculator-calculate_calories')  # URL for the custom calculate_calories action
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)  # It should not support GET, only POST


    def test_create_calorie_calculator_unauthenticated(self):
        """Test that an unauthenticated user cannot create a calorie calculator."""
        self.client.logout()  # Ensure the client is unauthenticated
        url = reverse('caloriecalculator-list')
        data = {
            'gender': 'male',
            'age': 30,
            'weight': 75,
            'height': 180,
            'activity_level': 'moderate_activity'
        }
        response = self.client.post(url, data, format='json')
        # Expect 401 Unauthorized because the user is not authenticated
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_calorie_calculator_authenticated(self):
        """Test that an authenticated user can create a calorie calculator."""
        self.client.force_authenticate(user=self.user)
        url = reverse('caloriecalculator-list')
        data = {
            'gender': 'male',
            'age': 30,
            'weight': 75,
            'height': 180,
            'activity_level': 'moderate_activity'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
