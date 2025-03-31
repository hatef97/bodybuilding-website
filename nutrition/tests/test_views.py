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
            fat=15,
            description="A healthy chicken salad.",
        )
        
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40,
            carbs=5,
            fat=25,
            description="Grilled salmon with vegetables.",
        )

        self.meal_3 = Meal.objects.create(
            name="Beef Steak",
            calories=800,
            protein=50,
            carbs=30,
            fat=40,
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
            'fat': 10,
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
            'fat': 10,
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
            'fat': 16,
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
        self.client.force_authenticate(user=self.regular_user)

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
                fat=10,
                description=f"Description of meal {i}",
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Should return 10 meals
        self.assertIn('next', response.data)  # Should have a 'next' page



class MealPlanViewSetTests(APITestCase):

    def setUp(self):
        """
        Set up initial data for the tests.
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
            password='userpassword',
        )

        # Create meal instances
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=35,
            carbs=10,
            fat=15,
            description="A healthy chicken salad."
        )
        
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40,
            carbs=5,
            fat=25,
            description="Grilled salmon with vegetables."
        )

        # Create a MealPlan instance associated with the admin user
        self.meal_plan = MealPlan.objects.create(
            user=self.regular_user,
            name="Weekly Plan",
            description="A plan with healthy meals"
        )
        # Add meals to the MealPlan
        self.meal_plan.meals.set([self.meal_1, self.meal_2])

        self.url = reverse('mealplan-list')  # Assuming this is the URL for the MealPlan viewset


    def test_meal_plan_list_authenticated_user(self):
        """
        Test that authenticated users can list meal plans.
        """
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only one meal plan for the user


    def test_meal_plan_list_unauthenticated_user(self):
        """
        Test that unauthenticated users cannot access the meal plan list.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_meal_plan_as_admin(self):
        """
        Test that an admin can create a meal plan.
        """
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'user': self.regular_user.id,
            'name': 'Weekly Plan 2',
            'description': 'A new weekly plan',
            'meals': [self.meal_1.id, self.meal_2.id],
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Weekly Plan 2')


    def test_create_meal_plan_as_regular_user(self):
        """
        Test that a regular user cannot create a meal plan.
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'user': self.regular_user.id,
            'name': 'Unauthorized Plan',
            'description': 'This plan should not be created',
            'meals': [self.meal_1.id, self.meal_2.id],
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_update_meal_plan_as_admin(self):
        """
        Test that an admin can update an existing meal plan.
        """
        # Ensure the client is authenticated as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Define the data to update
        data = {
            'name': 'Updated Meal Plan',
            'description': 'Updated description for meal plan',
            'meals': [self.meal_1.id],  # Assuming the meals should be updated as well
        }
        
        # Perform the update request
        response = self.client.put(reverse('mealplan-detail', kwargs={'pk': self.meal_plan.id}), data, format='json')
        
        # Check that the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the updated values in the response
        self.assertEqual(response.data['name'], 'Updated Meal Plan')
        self.assertEqual(response.data['description'], 'Updated description for meal plan')


    def test_update_meal_plan_as_regular_user(self):
        """
        Test that a regular user cannot update a meal plan created by another user.
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'Updated Meal Plan by Regular User',
            'description': 'Updated by regular user',
            'meals': [self.meal_1.id],
        }
        response = self.client.put(reverse('mealplan-detail', kwargs={'pk': self.meal_plan.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_meal_plan_delete_as_admin(self):
        """
        Test that an admin can delete a meal plan.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(reverse('mealplan-detail', kwargs={'pk': self.meal_plan.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MealPlan.objects.count(), 0)  # No meal plans should be left


    def test_meal_plan_delete_as_regular_user(self):
        """
        Test that a regular user cannot delete a meal plan.
        """
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(reverse('mealplan-detail', kwargs={'pk': self.meal_plan.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_invalid_ordering_field(self):
        """
        Test that an invalid ordering field raises a validation error.
        """
        self.client.force_authenticate(user=self.regular_user)

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
        self.client.force_authenticate(user=self.regular_user)

        # Perform the search query (search by meal plan name)
        response = self.client.get(self.url, {'search': 'Weekly'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        self.assertEqual(response.data['results'][0]['name'], self.meal_plan.name)


    def test_pagination(self):
        """
        Test that pagination works and only 10 items are returned per page.
        """
        self.client.force_authenticate(user=self.regular_user)
        for i in range(15):
            MealPlan.objects.create(
                user=self.regular_user,
                name=f"Plan {i}",
                description=f"Description of meal plan {i}"
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Should return 10 meal plans
        self.assertIn('next', response.data)  # Should have a 'next' page



class RecipeViewSetTests(APITestCase):

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
            password='userpassword',
        )

        # Create a meal instance for recipe association
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=35,
            carbs=10,
            fat=15,
            description="A healthy chicken salad."
        )

        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40,
            carbs=5,
            fat=25,
            description="Grilled salmon with vegetables."
        )

        # Create a recipe instance associated with the meal
        self.recipe_1 = Recipe.objects.create(
            meal=self.meal_1,
            instructions="Cook chicken and mix with salad ingredients.",
            ingredients="Chicken, Lettuce, Tomatoes, Olive Oil"
        )
        
        self.recipe_2 = Recipe.objects.create(
            meal=self.meal_2,
            instructions="Grill salmon and serve with veggies.",
            ingredients="Salmon, Broccoli, Olive Oil"
        )

        self.url = reverse('recipe-list')  # Assuming this is the URL for the Recipe viewset


    def test_recipe_list_authenticated_user(self):
        """
        Test that authenticated users can list recipes.
        """
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Should return 2 recipes


    def test_recipe_list_unauthenticated_user(self):
        """
        Test that unauthenticated users cannot access the recipe list.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_recipe_as_admin(self):
        """
        Test that an admin can create a recipe.
        """
        self.client.force_authenticate(user=self.admin_user)  # Ensure we authenticate as the admin user
        data = {
            'meal': self.meal_1.id,  # Ensure we are passing the meal ID, not the meal object
            'instructions': 'Cook chicken and mix with veggies.',
            'ingredients': 'Chicken, Lettuce, Carrot, Olive Oil'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['meal'], self.meal_1.id)
        self.assertEqual(response.data['instructions'], 'Cook chicken and mix with veggies.')
        

    def test_create_recipe_as_regular_user(self):
        """
        Test that a regular user cannot create a recipe.
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'meal': self.meal_2.id,
            'instructions': 'Grill salmon and serve with veggies.',
            'ingredients': 'Salmon, Broccoli, Olive Oil'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_update_recipe_as_admin(self):
        """
        Test that an admin can update a recipe.
        """
        self.client.force_authenticate(user=self.admin_user)  # Ensure we authenticate as the admin user

        # Prepare data to update the recipe
        data = {
            'meal': self.meal_1.id,  # Pass the meal ID correctly
            'instructions': 'Updated instructions for Chicken Salad.',
            'ingredients': 'Chicken, Lettuce, Tomatoes, Olive Oil, Cucumber'
        }

        # Perform the PUT request to update the recipe
        response = self.client.put(reverse('recipe-detail', kwargs={'pk': self.recipe_1.id}), data, format='json')

        # Assert that the update was successful and the recipe data was updated correctly
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Ensure the status code is 200 OK
        self.assertEqual(response.data['instructions'], 'Updated instructions for Chicken Salad.')
        self.assertEqual(response.data['ingredients'], 'Chicken, Lettuce, Tomatoes, Olive Oil, Cucumber')
        

    def test_update_recipe_as_regular_user(self):
        """
        Test that a regular user cannot update a recipe.
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'instructions': 'Updated instructions for Chicken Salad.',
            'ingredients': 'Chicken, Lettuce, Tomatoes, Olive Oil, Cucumber'
        }
        response = self.client.put(reverse('recipe-detail', kwargs={'pk': self.recipe_1.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_delete_recipe_as_admin(self):
        """
        Test that an admin can delete a recipe.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(reverse('recipe-detail', kwargs={'pk': self.recipe_1.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.count(), 1)  # Only one recipe should remain


    def test_delete_recipe_as_regular_user(self):
        """
        Test that a regular user cannot delete a recipe.
        """
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(reverse('recipe-detail', kwargs={'pk': self.recipe_1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_recipe_string_representation(self):
        """
        Test that the string representation of a recipe is correct.
        """
        self.assertEqual(str(self.recipe_1), f"Recipe for {self.meal_1.name}")  # Should return "Recipe for Chicken Salad"


    def test_pagination(self):
        """
        Test that pagination works and only 10 items are returned per page.
        """
        self.client.force_authenticate(user=self.regular_user)
        for i in range(15):
            Recipe.objects.create(
                meal=self.meal_1,
                instructions=f"Recipe {i} instructions.",
                ingredients=f"Ingredient {i}"
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Should return 10 recipes per page
        self.assertIn('next', response.data)  # Should have a 'next' page


    def test_search_functionality(self):
        """
        Test that the search query works correctly.
        """
        self.client.force_authenticate(user=self.regular_user)

        # Perform the search query (search by recipe instructions)
        response = self.client.get(self.url, {'search': 'Chicken'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        self.assertEqual(response.data['results'][0]['instructions'], self.recipe_1.instructions)
