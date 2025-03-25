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



class RecipeSerializerTests(APITestCase):
    
    def setUp(self):
        """
        Set up initial data for the tests. This will create some test data to work with.
        """
        # Create a sample Recipe object
        self.recipe_data = {
            'name': 'Chicken Salad',
            'ingredients': 'Chicken, lettuce, olive oil, vinegar',
            'instructions': 'Mix all ingredients in a bowl.',
            'calories': 350,
            'protein': 30.5,
            'carbs': 10.0,
            'fats': 15.0
        }
        self.recipe = Recipe.objects.create(**self.recipe_data)


    def test_recipe_serializer_valid_data(self):
        """
        Test that the serializer correctly serializes valid data.
        """
        # Assuming the 'recipe' instance exists with valid data
        serializer = RecipeSerializer(instance=self.recipe)
        data = serializer.data
        
        # Check that the name and fields match the expected values
        self.assertEqual(data['name'], self.recipe_data['name'])  # Check that the 'name' is correctly serialized
        self.assertEqual(data['ingredients'], self.recipe_data['ingredients'])  # Check ingredients
        self.assertEqual(data['instructions'], self.recipe_data['instructions'])  # Check instructions
        self.assertEqual(data['calories'], self.recipe_data['calories'])  # Check calories
        self.assertEqual(str(data['protein']).rstrip('0').rstrip('.'), str(self.recipe_data['protein']).rstrip('0').rstrip('.'))  # Check protein (Decimal comparison)
        self.assertEqual(str(data['carbs']).rstrip('0').rstrip('.'), str(self.recipe_data['carbs']).rstrip('0').rstrip('.'))  # Check carbs (Decimal comparison)
        self.assertEqual(str(data['fats']).rstrip('0').rstrip('.'), str(self.recipe_data['fats']).rstrip('0').rstrip('.'))  # Check fats (Decimal comparison)


    def test_recipe_serializer_invalid_negative_calories(self):
        """
        Test that negative calories raise a validation error.
        """
        data = self.recipe_data.copy()
        data['calories'] = -100  # Invalid negative calories
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to negative calories
        self.assertIn('calories', serializer.errors)  # Ensure the 'calories' field is in the errors
        self.assertEqual(serializer.errors['calories'][0], 'This field must be a positive value.')  # Check the error message


    def test_recipe_serializer_invalid_negative_protein(self):
        """
        Test that negative protein values raise a validation error.
        """
        data = self.recipe_data.copy()
        data['protein'] = -20.5  # Invalid negative protein value
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to negative protein
        self.assertIn('protein', serializer.errors)  # Ensure the 'protein' field is in the errors
        self.assertEqual(serializer.errors['protein'][0], 'This field must be a positive value.')  # Check the error message


    def test_recipe_serializer_invalid_negative_carbs(self):
        """
        Test that negative carbs values raise a validation error.
        """
        data = self.recipe_data.copy()
        data['carbs'] = -5.0  # Invalid negative carbs value
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to negative carbs
        self.assertIn('carbs', serializer.errors)  # Ensure the 'carbs' field is in the errors
        self.assertEqual(serializer.errors['carbs'][0], 'This field must be a positive value.')  # Check the error message


    def test_recipe_serializer_invalid_negative_fats(self):
        """
        Test that negative fats values raise a validation error.
        """
        data = self.recipe_data.copy()
        data['fats'] = -10.0  # Invalid negative fats value
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to negative fats
        self.assertIn('fats', serializer.errors)  # Ensure the 'fats' field is in the errors
        self.assertEqual(serializer.errors['fats'][0], 'This field must be a positive value.')  # Check the error message


    def test_recipe_serializer_missing_required_fields(self):
        """
        Test that missing required fields raise a validation error.
        """
        data = {}  # Missing all fields
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing fields
        self.assertIn('name', serializer.errors)  # Ensure the 'name' field is in the errors
        self.assertIn('ingredients', serializer.errors)  # Ensure the 'ingredients' field is in the errors
        self.assertIn('instructions', serializer.errors)  # Ensure the 'instructions' field is in the errors
        self.assertIn('calories', serializer.errors)  # Ensure the 'calories' field is in the errors
        self.assertIn('protein', serializer.errors)  # Ensure the 'protein' field is in the errors
        self.assertIn('carbs', serializer.errors)  # Ensure the 'carbs' field is in the errors
        self.assertIn('fats', serializer.errors)  # Ensure the 'fats' field is in the errors


    def test_recipe_serializer_missing_name(self):
        """
        Test that missing the name field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['name']  # Remove the 'name' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'name'
        self.assertIn('name', serializer.errors)  # Ensure the 'name' field is in the errors


    def test_recipe_serializer_missing_ingredients(self):
        """
        Test that missing the ingredients field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['ingredients']  # Remove the 'ingredients' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'ingredients'
        self.assertIn('ingredients', serializer.errors)  # Ensure the 'ingredients' field is in the errors


    def test_recipe_serializer_missing_instructions(self):
        """
        Test that missing the instructions field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['instructions']  # Remove the 'instructions' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'instructions'
        self.assertIn('instructions', serializer.errors)  # Ensure the 'instructions' field is in the errors


    def test_recipe_serializer_missing_calories(self):
        """
        Test that missing the calories field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['calories']  # Remove the 'calories' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'calories'
        self.assertIn('calories', serializer.errors)  # Ensure the 'calories' field is in the errors


    def test_recipe_serializer_missing_protein(self):
        """
        Test that missing the protein field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['protein']  # Remove the 'protein' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'protein'
        self.assertIn('protein', serializer.errors)  # Ensure the 'protein' field is in the errors


    def test_recipe_serializer_missing_carbs(self):
        """
        Test that missing the carbs field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['carbs']  # Remove the 'carbs' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'carbs'
        self.assertIn('carbs', serializer.errors)  # Ensure the 'carbs' field is in the errors


    def test_recipe_serializer_missing_fats(self):
        """
        Test that missing the fats field raises a validation error.
        """
        data = self.recipe_data.copy()
        del data['fats']  # Remove the 'fats' field
        
        serializer = RecipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # The serializer should be invalid due to missing 'fats'
        self.assertIn('fats', serializer.errors)  # Ensure the 'fats' field is in the errors



class CalorieCalculatorSerializerTests(APITestCase):
    
    def setUp(self):
        """
        Set up initial data for tests.
        """
        # Create a sample calorie calculator instance
        self.calorie_calculator_data = {
            'gender': 'male',
            'age': 30,
            'weight': 75.0,
            'height': 180.0,
            'activity_level': 'moderate_activity',
            'goal': 'maintain'
        }
        self.calorie_calculator = CalorieCalculator.objects.create(**self.calorie_calculator_data)
        

    def test_calorie_calculator_serializer_valid_data(self):
        """
        Test that the serializer correctly serializes valid data.
        """
        # Create a serializer instance
        serializer = CalorieCalculatorSerializer(self.calorie_calculator)
        
        # Serialize the data
        data = serializer.data
        
        # Check the serialized data
        self.assertEqual(data['gender'], self.calorie_calculator_data['gender'])
        self.assertEqual(data['age'], self.calorie_calculator_data['age'])
        self.assertEqual(data['weight'], self.calorie_calculator_data['weight'])
        self.assertEqual(data['height'], self.calorie_calculator_data['height'])
        self.assertEqual(data['activity_level'], self.calorie_calculator_data['activity_level'])
        self.assertEqual(data['goal'], self.calorie_calculator_data['goal'])
    

    def test_calorie_calculator_serializer_invalid_age(self):
        """
        Test that invalid age raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['age'] = -1  # Invalid age
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)
        self.assertEqual(serializer.errors['age'][0], 'This field must be a positive value.')
    

    def test_calorie_calculator_serializer_invalid_weight(self):
        """
        Test that invalid weight raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['weight'] = -50.0  # Invalid weight
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)
        self.assertEqual(serializer.errors['weight'][0], 'This field must be a positive value.')
    

    def test_calorie_calculator_serializer_invalid_height(self):
        """
        Test that invalid height raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['height'] = -150.0  # Invalid height
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('height', serializer.errors)
        self.assertEqual(serializer.errors['height'][0], 'This field must be a positive value.')
    

    def test_calorie_calculator_serializer_invalid_gender(self):
        """
        Test that an invalid gender raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['gender'] = 'invalid_gender'  # Invalid gender
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('gender', serializer.errors)
        self.assertEqual(serializer.errors['gender'][0], '"invalid_gender" is not a valid choice.')


    def test_calorie_calculator_calculate_calories(self):
        """
        Test that the calorie calculation is correct based on the Harris-Benedict formula.
        """
        # Create a new calorie calculator instance
        calorie_calculator = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75.0,
            height=180.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        
        # Calculate expected calories using the Harris-Benedict formula
        expected_bmr = 10 * calorie_calculator.weight + 6.25 * calorie_calculator.height - 5 * calorie_calculator.age + 5
        expected_calories = expected_bmr * 1.55  # Moderate activity multiplier
        
        # Create serializer instance
        serializer = CalorieCalculatorSerializer(calorie_calculator)
        
        # Check if the calculated calories match the expected value
        self.assertEqual(serializer.calculate_calories(calorie_calculator), expected_calories)


    def test_calorie_calculator_serializer_missing_required_fields(self):
        """
        Test that missing required fields raise validation errors.
        """
        data = {
            'gender': 'male',
            # Missing required fields: age, weight, height, activity_level, goal
        }
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid due to missing required fields
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)
        self.assertIn('weight', serializer.errors)
        self.assertIn('height', serializer.errors)
        self.assertIn('activity_level', serializer.errors)
        self.assertIn('goal', serializer.errors)


    def test_calorie_calculator_serializer_invalid_goal(self):
        """
        Test that an invalid goal raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['goal'] = 'invalid_goal'  # Invalid goal
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('goal', serializer.errors)
        self.assertEqual(serializer.errors['goal'][0], '"invalid_goal" is not a valid choice.')


    def test_calorie_calculator_serializer_invalid_activity_level(self):
        """
        Test that an invalid activity level raises a validation error.
        """
        data = self.calorie_calculator_data.copy()
        data['activity_level'] = 'invalid_activity_level'  # Invalid activity level
        
        serializer = CalorieCalculatorSerializer(data=data)
        
        # Check if the serializer is invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('activity_level', serializer.errors)
        self.assertEqual(serializer.errors['activity_level'][0], '"invalid_activity_level" is not a valid choice.')



class MealPlanSummarySerializerTests(APITestCase):
    """
    Tests for MealPlanSummarySerializer
    """

    def setUp(self):
        """
        Set up the initial data for the tests.
        """
        # Create sample meals
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=35.0,
            carbs=10.0,
            fats=15.0,
            description="A healthy chicken salad."
        )
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=40.0,
            carbs=5.0,
            fats=25.0,
            description="Grilled salmon with vegetables."
        )
        
        # Create meal plan and add meals to it
        self.meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",
            goal="bulking"
        )
        self.meal_plan.meals.add(self.meal_1, self.meal_2)


    def test_meal_plan_summary_serializer_valid_data(self):
        """
        Test that the serializer correctly summarizes meal plan data.
        """
        # Create serializer instance using the meal plan's meals
        serializer = MealPlanSummarySerializer(data={
            'total_calories': 400 + 500,
            'total_protein': 35.0 + 40.0,
            'total_carbs': 10.0 + 5.0,
            'total_fats': 15.0 + 25.0
        })

        # Validate if the data is correct
        self.assertTrue(serializer.is_valid())
        
        # Test the serialized output against expected totals
        data = serializer.data
        self.assertEqual(data['total_calories'], 900)
        self.assertEqual(data['total_protein'], 75.0)
        self.assertEqual(data['total_carbs'], 15.0)
        self.assertEqual(data['total_fats'], 40.0)


    def test_meal_plan_summary_serializer_invalid_data(self):
        """
        Test that the serializer rejects invalid data.
        """
        # Provide invalid data (negative values)
        serializer = MealPlanSummarySerializer(data={
            'total_calories': -900,  # Invalid negative calories
            'total_protein': -75.0,  # Invalid negative protein
            'total_carbs': -15.0,    # Invalid negative carbs
            'total_fats': -40.0      # Invalid negative fats
        })

        # Assert that the serializer is invalid and errors exist
        self.assertFalse(serializer.is_valid())

        # Check that the correct errors exist for each field
        self.assertIn('total_calories', serializer.errors)
        self.assertIn('total_protein', serializer.errors)
        self.assertIn('total_carbs', serializer.errors)
        self.assertIn('total_fats', serializer.errors)

        # Assert the error messages for each field
        self.assertEqual(serializer.errors['total_calories'][0], "This field must be a positive value.")
        self.assertEqual(serializer.errors['total_protein'][0], "This field must be a positive value.")
        self.assertEqual(serializer.errors['total_carbs'][0], "This field must be a positive value.")
        self.assertEqual(serializer.errors['total_fats'][0], "This field must be a positive value.")
        

    def test_meal_plan_summary_serializer_missing_fields(self):
        """
        Test that the serializer raises an error if required fields are missing.
        """
        # Missing required fields, only sending 'total_calories'
        serializer = MealPlanSummarySerializer(data={
            'total_calories': 900
        })

        # Assert that the serializer is invalid because some fields are missing
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_protein', serializer.errors)
        self.assertIn('total_carbs', serializer.errors)
        self.assertIn('total_fats', serializer.errors)


    def test_meal_plan_summary_serializer_empty_data(self):
        """
        Test that the serializer raises an error if no data is provided.
        """
        serializer = MealPlanSummarySerializer(data={})

        # Assert that the serializer is invalid and errors are present for all fields
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_calories', serializer.errors)
        self.assertIn('total_protein', serializer.errors)
        self.assertIn('total_carbs', serializer.errors)
        self.assertIn('total_fats', serializer.errors)


    def test_meal_plan_summary_serializer_calculation_from_meals(self):
        """
        Test that the serializer can calculate total values from associated meals.
        """
        # Manually calculate the totals from meals
        total_calories = self.meal_1.calories + self.meal_2.calories
        total_protein = self.meal_1.protein + self.meal_2.protein
        total_carbs = self.meal_1.carbs + self.meal_2.carbs
        total_fats = self.meal_1.fats + self.meal_2.fats
        
        # Create the MealPlanSummary instance
        meal_plan_data = {
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fats': total_fats
        }

        # Serialize and validate
        serializer = MealPlanSummarySerializer(data=meal_plan_data)
        self.assertTrue(serializer.is_valid())
        
        # Ensure the serialized values match the manually calculated totals
        data = serializer.data
        self.assertEqual(data['total_calories'], total_calories)
        self.assertEqual(data['total_protein'], total_protein)
        self.assertEqual(data['total_carbs'], total_carbs)
        self.assertEqual(data['total_fats'], total_fats)
