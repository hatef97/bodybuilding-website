from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from django.urls import reverse
from core.models import CustomUser as User

from nutrition.models import *
from nutrition.serializers import *



class MealViewSetTests(APITestCase):
    
    def setUp(self):
        """
        Set up the initial data for the tests.
        """
        # Create sample users: one admin and one regular user
        self.admin_user = User.objects.create_superuser(
            email='admin1@mail.com',
            username='admin1',
            password='admin1password',
            )
        self.regular_user = User.objects.create_user(
            email='user@mail.com',
            username='user',
            password='userpassword'
            )
        
        # Create sample meals
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=35,
            carbs=10,
            fats=15,
            description="A healthy chicken salad.",
        )
        
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40,
            carbs=5,
            fats=25,
            description="Grilled salmon with vegetables.",
        )

        self.meal_3 = Meal.objects.create(
            name="Beef Steak",
            calories=800,
            protein=50,
            carbs=30,
            fats=40,
            description="A juicy beef steak.",
        )
        
        self.url = reverse('meal-list')  # Assuming the URL for the Meal viewset is 'meal-list'


    def test_meal_list_authenticated_user(self):
        """
        Test that an authenticated user can list meals.
        """
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # Should return 3 meals


    def test_meal_list_unauthenticated_user(self):
        """
        Test that an unauthenticated user cannot access the meal list.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_meal_as_admin(self):
        """
        Test that an admin can create a meal.
        """
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Vegan Burger',
            'calories': 350,
            'protein': 25,
            'carbs': 40,
            'fats': 10,
            'description': 'A healthy vegan burger.',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Vegan Burger')


    def test_create_meal_as_regular_user(self):
        """
        Test that a regular user cannot create a meal.
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'Vegan Burger',
            'calories': 350,
            'protein': 25,
            'carbs': 40,
            'fats': 10,
            'description': 'A healthy vegan burger.',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_update_meal_as_admin(self):
        """
        Test that an admin can update a meal.
        """
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Updated Chicken Salad',
            'calories': 420,
            'protein': 37,
            'carbs': 12,
            'fats': 16,
            'description': 'Updated description for chicken salad.',
        }
        response = self.client.put(reverse('meal-detail', kwargs={'pk': self.meal_1.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Chicken Salad')


    def test_delete_meal_as_admin(self):
        """
        Test that an admin can delete a meal.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(reverse('meal-detail', kwargs={'pk': self.meal_1.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Meal.objects.count(), 2)  # Only 2 meals should remain


    def test_invalid_ordering_field(self):
        """
        Test that an invalid ordering field raises a validation error.
        """
        # Authenticate the user
        self.client.force_authenticate(user=self.regular_user)  # Assuming regular_user is defined in setUp()

        # Perform a GET request with an invalid ordering field
        response = self.client.get(self.url, {'ordering': 'invalid_field'}, format='json')

        # Check that the status code is 400 Bad Request (since invalid ordering should result in validation error)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check the error message directly in the response
        self.assertIn('Invalid ordering field', str(response.data))  # Ensure the error message is in the response data


    def test_search_functionality(self):
        """
        Test that the search query works correctly.
        """
        # Manually authenticate the user
        self.client.force_authenticate(user=self.regular_user)

        # Perform the search query (search by meal name)
        response = self.client.get(self.url, {'search': 'Chicken'}, format='json')

        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the meal is in the response
        self.assertGreater(len(response.data['results']), 0)  # Expecting at least one meal in the response
        self.assertEqual(response.data['results'][0]['name'], self.meal_1.name)  # Verify that the correct meal is returned


    def test_pagination(self):
        """
        Test that pagination works and only 10 items are returned per page.
        """
        self.client.force_authenticate(user=self.regular_user)
        for i in range(15):
            Meal.objects.create(
                name=f"Meal {i}",
                calories=300,
                protein=20,
                carbs=25,
                fats=10,
                description=f"Description of meal {i}",
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Should return 10 meals
        self.assertIn('next', response.data)  # Should have a 'next' page


    def test_meal_plan_summary_serializer(self):
        """
        Test that the meal plan summary returns the correct calculated values.
        """
        # Set up data to check for meal summary
        total_calories = 900
        total_protein = 75.0
        total_carbs = 50.0
        total_fats = 30.0

        data = {
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fats': total_fats
        }

        serializer = MealPlanSummarySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total_calories'], total_calories)
        self.assertEqual(serializer.validated_data['total_protein'], total_protein)
        self.assertEqual(serializer.validated_data['total_carbs'], total_carbs)
        self.assertEqual(serializer.validated_data['total_fats'], total_fats)
