from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status

from nutrition.models import Meal
from nutrition.serializers import MealSerializer



class MealSerializerTests(APITestCase):

    def setUp(self):
        """
        Set up initial data for the tests. Create a few meals with different macronutrient values.
        """
        self.valid_meal_data = {
            "name": "Chicken Salad",
            "calories": 400,
            "protein": Decimal('30.00'),
            "carbs": Decimal('10.00'),
            "fats": Decimal('15.00'),
            "description": "A healthy chicken salad."
        }
        
        self.invalid_meal_data_negative_protein = {
            "name": "Invalid Meal",
            "calories": 300,
            "protein": Decimal('-5.00'),
            "carbs": Decimal('20.00'),
            "fats": Decimal('10.00'),
            "description": "This meal has negative protein."
        }

        self.invalid_meal_data_negative_carbs = {
            "name": "Invalid Meal",
            "calories": 300,
            "protein": Decimal('15.00'),
            "carbs": Decimal('-10.00'),
            "fats": Decimal('10.00'),
            "description": "This meal has negative carbs."
        }

        self.invalid_meal_data_negative_fats = {
            "name": "Invalid Meal",
            "calories": 300,
            "protein": Decimal('15.00'),
            "carbs": Decimal('20.00'),
            "fats": Decimal('-10.00'),
            "description": "This meal has negative fats."
        }

        self.meal = Meal.objects.create(**self.valid_meal_data)


    def test_meal_serializer_valid_data(self):
        """
        Test that the MealSerializer works correctly for valid data.
        """
        serializer = MealSerializer(data=self.valid_meal_data)
        self.assertTrue(serializer.is_valid())  # Ensure the data is valid
        meal = serializer.save()  # Save the meal
        self.assertEqual(meal.name, "Chicken Salad")  # Check if the name is saved correctly
        self.assertEqual(meal.calories, 400)  # Check if calories are correct
        self.assertEqual(meal.protein, Decimal('30.00'))  # Check if protein is correct
        self.assertEqual(meal.carbs, Decimal('10.00'))  # Check if carbs are correct
        self.assertEqual(meal.fats, Decimal('15.00'))  # Check if fats are correct
        self.assertEqual(meal.description, "A healthy chicken salad.")  # Check description


    def test_meal_serializer_negative_protein(self):
        """
        Test that MealSerializer rejects negative protein values.
        """
        serializer = MealSerializer(data=self.invalid_meal_data_negative_protein)
        self.assertFalse(serializer.is_valid())  # Ensure the data is invalid
        self.assertEqual(serializer.errors['protein'][0], "This field must be a positive value.")  # Validate the error message


    def test_meal_serializer_negative_carbs(self):
        """
        Test that MealSerializer rejects negative carbs values.
        """
        serializer = MealSerializer(data=self.invalid_meal_data_negative_carbs)
        self.assertFalse(serializer.is_valid())  # Ensure the data is invalid
        self.assertEqual(serializer.errors['carbs'][0], "This field must be a positive value.")  # Validate the error message


    def test_meal_serializer_negative_fats(self):
        """
        Test that MealSerializer rejects negative fats values.
        """
        serializer = MealSerializer(data=self.invalid_meal_data_negative_fats)
        self.assertFalse(serializer.is_valid())  # Ensure the data is invalid
        self.assertEqual(serializer.errors['fats'][0], "This field must be a positive value.")  # Validate the error message


    def test_meal_serializer_required_fields(self):
        """
        Test that required fields are present in the serializer and handled correctly.
        """
        # Check if all fields are serialized correctly
        serializer = MealSerializer(self.meal)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('calories', data)
        self.assertIn('protein', data)
        self.assertIn('carbs', data)
        self.assertIn('fats', data)
        self.assertIn('description', data)


    def test_invalid_data_for_missing_fields(self):
        """
        Test if the serializer raises errors when required fields are missing.
        """
        invalid_data = {
            "name": "Invalid Meal",
            "calories": 400,
            "protein": Decimal('30.00'),
            "fats": Decimal('15.00'),
            "description": "Missing carbs value"
        }
        serializer = MealSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('carbs', serializer.errors)  # Carbs field is missing in the data
