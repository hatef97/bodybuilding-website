from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from nutrition.models import *
from nutrition.serializers import *



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



class MealPlanSerializerTests(APITestCase):

    def setUp(self):
        """
        Set up initial data for the tests. Create meals and a meal plan for testing.
        """
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=30.00,
            carbs=10.00,
            fats=15.00,
            description="A healthy chicken salad."
        )
        
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40.00,
            carbs=5.00,
            fats=25.00,
            description="Grilled salmon with vegetables."
        )

        self.meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",
            goal="bulking"
        )

        # Adding meals to the meal plan
        self.meal_plan.meals.add(self.meal_1, self.meal_2)

        self.valid_meal_plan_data = {
            'name': 'Bulking Meal Plan',
            'goal': 'bulking',
            'meals': [
                {'id': self.meal_1.id, 'name': 'Chicken Salad', 'calories': 400, 'protein': Decimal('30.00'), 'carbs': Decimal('10.00'), 'fats': Decimal('15.00')},
                {'id': self.meal_2.id, 'name': 'Grilled Salmon', 'calories': 500, 'protein': Decimal('40.00'), 'carbs': Decimal('5.00'), 'fats': Decimal('25.00')}
            ]
        }


    def test_meal_plan_serializer_valid_data(self):
        """
        Test that the MealPlanSerializer correctly serializes data and includes calculated totals.
        """
        serializer = MealPlanSerializer(self.meal_plan)
        data = serializer.data
        self.assertEqual(data['name'], "Bulking Meal Plan")
        self.assertEqual(data['goal'], "bulking")
        self.assertIn('meals', data)
        self.assertEqual(len(data['meals']), 2)
        
        # Check if total macronutrients are correctly calculated
        self.assertEqual(data['total_calories'], 400 + 500)  # Total calories: 400 + 500
        self.assertEqual(data['total_protein'], Decimal('30.00') + Decimal('40.00'))  # Total protein: 30 + 40
        self.assertEqual(data['total_carbs'], Decimal('10.00') + Decimal('5.00'))  # Total carbs: 10 + 5
        self.assertEqual(data['total_fats'], Decimal('15.00') + Decimal('25.00'))  # Total fats: 15 + 25


    def test_meal_plan_serializer_invalid_goal(self):
        """
        Test if invalid goal raises an error when creating a MealPlan.
        """
        invalid_data = {
            'name': 'Invalid Meal Plan',
            'goal': 'invalid_goal',  # Invalid goal
            'meals': [
                {'id': self.meal_1.id},
                {'id': self.meal_2.id}
            ]
        }

        serializer = MealPlanSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('goal', serializer.errors)  # Ensure 'goal' is in errors


    def test_meal_plan_serializer_no_meals(self):
        """
        Test that a MealPlan with no meals does not cause errors and has zero totals.
        """
        meal_plan_no_meals = MealPlan.objects.create(name="No Meals Plan", goal="cutting")
        serializer = MealPlanSerializer(meal_plan_no_meals)
        data = serializer.data
        
        self.assertEqual(data['name'], "No Meals Plan")
        self.assertEqual(data['goal'], "cutting")
        self.assertEqual(data['total_calories'], 0)
        self.assertEqual(data['total_protein'], Decimal('0.00'))
        self.assertEqual(data['total_carbs'], Decimal('0.00'))
        self.assertEqual(data['total_fats'], Decimal('0.00'))


    def test_meal_plan_serializer_missing_meal_fields(self):
        """
        Test if MealPlanSerializer raises an error when required fields in meals are missing.
        """
        data = {
            "name": "Test Meal Plan",
            "goal": "bulking",
            "meals": [
                {
                    "name": "Chicken Salad",
                    "calories": 400,
                    # Missing protein, carbs, and fats
                }
            ]
        }

        serializer = MealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing fields in the meal
        self.assertIn("meals", serializer.errors)  # Ensure meals field is in errors
        self.assertIn("protein", serializer.errors["meals"][0])  # Ensure protein is in the errors for the meal
        self.assertIn("carbs", serializer.errors["meals"][0])  # Ensure carbs is in the errors for the meal
        self.assertIn("fats", serializer.errors["meals"][0])  # Ensure fats is in the errors for the meal


    def test_meal_plan_serializer_meal_ordering(self):
        """
        Test that the meals in the MealPlan are correctly ordered based on the 'order' field.
        """
        # Ensure the meal doesn't already exist in the plan, to avoid IntegrityError
        if not MealInMealPlan.objects.filter(meal=self.meal_1, meal_plan=self.meal_plan).exists():
            meal_in_plan_1 = MealInMealPlan.objects.create(meal=self.meal_1, meal_plan=self.meal_plan, order=1)
        if not MealInMealPlan.objects.filter(meal=self.meal_2, meal_plan=self.meal_plan).exists():
            meal_in_plan_2 = MealInMealPlan.objects.create(meal=self.meal_2, meal_plan=self.meal_plan, order=2)
        
        # Now check if they are ordered properly
        meal_plan_serializer = MealPlanSerializer(self.meal_plan)
        
        meal_plan_data = meal_plan_serializer.data
        meal_ids_in_order = [meal['id'] for meal in meal_plan_data['meals']]
        
        # Ensure meals are ordered by the 'order' field
        self.assertEqual(meal_ids_in_order, [self.meal_1.id, self.meal_2.id])  # Correct order should be meal_1 first, meal_2 second


    def test_meal_plan_calculation_of_macros(self):
        """
        Test that macros (calories, protein, carbs, fats) are correctly calculated and returned.
        """
        meal_plan = MealPlan.objects.get(id=self.meal_plan.id)
        total_calories = sum([meal.calories for meal in meal_plan.meals.all()])
        total_protein = sum([meal.protein for meal in meal_plan.meals.all()])
        total_carbs = sum([meal.carbs for meal in meal_plan.meals.all()])
        total_fats = sum([meal.fats for meal in meal_plan.meals.all()])

        self.assertEqual(meal_plan.total_calories(), total_calories)
        self.assertEqual(meal_plan.total_protein(), total_protein)
        self.assertEqual(meal_plan.total_carbs(), total_carbs)
        self.assertEqual(meal_plan.total_fats(), total_fats)


class MealInMealPlanSerializerTests(APITestCase):
    
    def setUp(self):
        """
        Set up the initial data for the tests.
        """
        # Create a sample meal and meal plan
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=35,
            carbs=10,
            fats=15,
            description="A healthy chicken salad."
        )
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40,
            carbs=5,
            fats=25,
            description="Grilled salmon with vegetables."
        )
        self.meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",
            goal="bulking"
        )


    def test_meal_in_meal_plan_serializer_valid_data(self):
        """
        Test that the serializer correctly serializes valid data.
        """
        meal_in_plan = MealInMealPlan.objects.create(meal=self.meal_1, meal_plan=self.meal_plan, order=1)
        
        # Serialize the MealInMealPlan instance
        serializer = MealInMealPlanSerializer(meal_in_plan)
        data = serializer.data
        
        # Check the serialized meal data
        self.assertEqual(data['meal'], self.meal_1.id)  # Check that the 'meal' is just the ID (not full object)
        self.assertEqual(data['meal_plan'], self.meal_plan.id)
        self.assertEqual(data['order'], 1)


    def test_meal_in_meal_plan_serializer_invalid_order(self):
        """
        Test that an invalid order (negative or zero) raises a validation error.
        """
        # Test with negative order
        data = {
            "meal": self.meal_1.id,  # Only pass the meal ID here
            "meal_plan": self.meal_plan.id,  # Ensure you are using a valid meal plan ID
            "order": -1  # Invalid order
        }
        serializer = MealInMealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to the negative order
        self.assertIn("order", serializer.errors)  # Ensure the 'order' field is in the errors
        self.assertEqual(serializer.errors['order'][0], 'Ensure this value is greater than or equal to 1.')  # Check the error message

        # Test with zero order
        data["order"] = 0  # Invalid order (zero)
        serializer = MealInMealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to the zero order
        self.assertIn("order", serializer.errors)  # Ensure the 'order' field is in the errors
        self.assertEqual(serializer.errors['order'][0], 'Ensure this value is greater than or equal to 1.')  # Check the error message
        
        
    def test_meal_in_meal_plan_serializer_missing_order(self):
        """
        Test that the serializer raises an error if the order field is missing.
        """
        data = {
            "meal": self.meal_1.id,
            "meal_plan": self.meal_plan.id,
        }
        serializer = MealInMealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # Order is required
        self.assertIn('order', serializer.errors)


    def test_meal_in_meal_plan_serializer_missing_meal(self):
        """
        Test that the serializer raises an error if the meal field is missing.
        """
        data = {
            "meal_plan": self.meal_plan.id,
            "order": 1
        }
        serializer = MealInMealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # Meal is required
        self.assertIn('meal', serializer.errors)


    def test_meal_in_meal_plan_serializer_valid_order(self):
        """
        Test that the serializer correctly handles a valid order field.
        """
        data = {
            "meal": self.meal_1.id,  # Pass the meal ID
            "meal_plan": self.meal_plan.id,  # Ensure you're using a valid meal plan ID
            "order": 1  # Valid order
        }

        # Create the serializer instance
        serializer = MealInMealPlanSerializer(data=data)

        # Validate if the serializer is valid
        self.assertTrue(serializer.is_valid())  # Valid order should pass

        # Save the instance and check that the order is correct
        meal_in_plan = serializer.save()
        self.assertEqual(meal_in_plan.order, 1)


    def test_meal_in_meal_plan_serializer_order_validation(self):
        """
        Test that the custom validation for the 'order' field works as expected.
        """
        data = {
            "meal": self.meal_1.id,
            "meal_plan": self.meal_plan.id,
            "order": -1  # Invalid order
        }
        serializer = MealInMealPlanSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # Invalid order should fail validation
        self.assertIn('order', serializer.errors)
        self.assertEqual(serializer.errors['order'][0], 'Ensure this value is greater than or equal to 1.')


    def test_meal_in_meal_plan_serializer_duplicate_meal_in_plan(self):
        """
        Test that duplicate entries (meal already added to the plan) are not allowed.
        """
        # Add a meal to the meal plan
        MealInMealPlan.objects.create(meal=self.meal_1, meal_plan=self.meal_plan, order=1)

        # Try to add the same meal to the same meal plan again
        data = {
            "meal": self.meal_1.id,  # Send only the meal ID
            "meal_plan": self.meal_plan.id,  # Same meal plan
            "order": 2  # Different order
        }

        serializer = MealInMealPlanSerializer(data=data)

        # Ensure the serializer is not valid due to duplicate meal in plan
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)  # Check for non_field_errors
        self.assertEqual(serializer.errors["non_field_errors"][0], "The fields meal_plan, meal must make a unique set.")  # Updated error message
        

    def test_meal_in_meal_plan_serializer_order_update(self):
        """
        Test if the order can be updated correctly.
        """
        meal_in_plan = MealInMealPlan.objects.create(meal=self.meal_1, meal_plan=self.meal_plan, order=1)
        meal_in_plan.order = 2  # Update order
        meal_in_plan.save()
        
        # Serialize and check the updated order
        serializer = MealInMealPlanSerializer(meal_in_plan)
        data = serializer.data
        self.assertEqual(data['order'], 2)
