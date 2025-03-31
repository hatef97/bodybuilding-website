from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from django.core.exceptions import ValidationError as DjangoValidationError

from core.models import CustomUser as User
from nutrition.models import *
from nutrition.serializers import *



class CalorieCalculatorSerializerTestCase(APITestCase):

    def setUp(self):
        """
        Create a sample CalorieCalculator instance for testing.
        """
        self.valid_data = {
            'gender': 'male',
            'age': 30,
            'weight': 75,
            'height': 175,
            'activity_level': 'moderate_activity'
        }
        self.invalid_data = {
            'gender': 'unknown',
            'age': -1,
            'weight': 0,
            'height': -175,
            'activity_level': 'extreme'
        }
    

    def test_calorie_calculator_serializer_valid_data(self):
        """
        Test that the CalorieCalculator serializer works with valid data.
        """
        serializer = CalorieCalculatorSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        self.assertEqual(serializer.validated_data['gender'], 'male')
        self.assertEqual(serializer.validated_data['age'], 30)
        self.assertEqual(serializer.validated_data['weight'], 75)
        self.assertEqual(serializer.validated_data['height'], 175)
        self.assertEqual(serializer.validated_data['activity_level'], 'moderate_activity')
    

    def test_calorie_calculator_serializer_invalid_data(self):
        """
        Test that the CalorieCalculator serializer raises validation errors for invalid data.
        """
        serializer = CalorieCalculatorSerializer(data=self.invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Expecting a ValidationError
    

    def test_calorie_calculator_create(self):
        """
        Test that the `create` method works as expected and calculates calories.
        """
        # Create the serializer with valid data
        serializer = CalorieCalculatorSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()

        # Calculate the expected BMR and apply the activity level multiplier
        expected_bmr = 10 * 75 + 6.25 * 175 - 5 * 30 + 5  # BMR for a male
        expected_calories = expected_bmr * 1.55  # Activity multiplier for moderate activity (1.55)

        # Check if the calculated calories are as expected
        self.assertAlmostEqual(instance.calculate_calories(), expected_calories, places=2)


    def test_calorie_calculator_invalid_age(self):
        """
        Test that a ValidationError is raised for invalid age.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['age'] = -1  # Invalid age
        serializer = CalorieCalculatorSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_calorie_calculator_invalid_weight(self):
        """
        Test that a ValidationError is raised for invalid weight.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['weight'] = 0  # Invalid weight
        serializer = CalorieCalculatorSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)
    

    def test_calorie_calculator_invalid_height(self):
        """
        Test that a ValidationError is raised for invalid height.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['height'] = -175  # Invalid height
        serializer = CalorieCalculatorSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)
    

    def test_calorie_calculator_invalid_gender(self):
        """
        Test that a ValidationError is raised for invalid gender.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['gender'] = 'unknown'  # Invalid gender
        serializer = CalorieCalculatorSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


    def test_calorie_calculator_invalid_activity_level(self):
        """
        Test that a ValidationError is raised for an invalid activity level.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['activity_level'] = 'extreme'  # Invalid activity level
        serializer = CalorieCalculatorSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)
    

    def test_calorie_calculator_default_values(self):
        """
        Test that the default values for gender, activity level, etc., are properly set when not provided.
        """
        # Create a valid input with missing 'gender' and 'activity_level'
        data_without_optional_fields = {
            'age': 30,
            'weight': 75,
            'height': 175
        }

        # Serialize the data without 'gender' and 'activity_level'
        serializer = CalorieCalculatorSerializer(data=data_without_optional_fields)
        
        # Validate the serializer
        self.assertTrue(serializer.is_valid())  # Should work since the default gender and activity_level will be used
        
        # Verify the defaults are applied
        self.assertEqual(serializer.validated_data['gender'], 'male')  # Default gender should be 'male'
        self.assertEqual(serializer.validated_data['activity_level'], 'sedentary')  # Default activity level should be 'sedentary'
    

    def test_calorie_calculator_missing_required_field(self):
        """
        Test that a required field is missing and raises a validation error.
        """
        data_missing_age = self.valid_data.copy()
        del data_missing_age['age']  # Remove the age field to test missing required field
        serializer = CalorieCalculatorSerializer(data=data_missing_age)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)



class MealSerializerTestCase(APITestCase):

    def setUp(self):
        """
        Create a valid Meal instance for testing.
        """
        self.valid_data = {
            'name': 'Chicken Salad',
            'description': 'A healthy chicken salad',
            'calories': 250,
            'protein': 30,
            'carbs': 15,
            'fat': 10
        }

        self.invalid_data = {
            'name': 'Invalid Meal',
            'description': 'Invalid meal test',
            'calories': -100,  # Invalid negative calories
            'protein': 10,
            'carbs': 20,
            'fat': 5
        }


    def test_meal_serializer_valid_data(self):
        """
        Test that the MealSerializer works with valid data.
        """
        serializer = MealSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        self.assertEqual(serializer.validated_data['name'], 'Chicken Salad')
        self.assertEqual(serializer.validated_data['calories'], 250)


    def test_meal_serializer_invalid_calories(self):
        """
        Test that the MealSerializer raises a validation error for invalid calories.
        """
        serializer = MealSerializer(data=self.invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Expecting a ValidationError for negative calories


    def test_meal_serializer_missing_name(self):
        """
        Test that the MealSerializer raises a validation error if the name field is missing.
        """
        data_missing_name = self.valid_data.copy()
        del data_missing_name['name']  # Remove the 'name' field to simulate missing data
        serializer = MealSerializer(data=data_missing_name)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for missing 'name'


    def test_meal_serializer_missing_calories(self):
        """
        Test that the MealSerializer raises a validation error if calories field is missing.
        """
        data_missing_calories = self.valid_data.copy()
        del data_missing_calories['calories']  # Remove the 'calories' field to simulate missing data
        serializer = MealSerializer(data=data_missing_calories)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for missing 'calories'


    def test_meal_serializer_negative_calories(self):
        """
        Test that the MealSerializer raises a validation error for negative calories.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['calories'] = -50  # Set negative calories
        serializer = MealSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for negative calories


    def test_meal_serializer_zero_calories(self):
        """
        Test that the MealSerializer raises a validation error for zero calories.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['calories'] = 0  # Set zero calories
        serializer = MealSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for zero calories


    def test_meal_serializer_serialize_valid_data(self):
        """
        Test that valid data can be serialized into a valid meal object.
        """
        meal = Meal.objects.create(**self.valid_data)  # Create a Meal instance
        serializer = MealSerializer(meal)
        self.assertEqual(serializer.data['name'], 'Chicken Salad')
        self.assertEqual(serializer.data['calories'], 250)


    def test_meal_serializer_deserialize_and_create(self):
        """
        Test that the MealSerializer correctly deserializes and creates a new Meal instance.
        """
        serializer = MealSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        meal_instance = serializer.save()  # Save the new meal instance
        
        # Fetch the meal instance from the database and assert its fields
        meal_from_db = Meal.objects.get(id=meal_instance.id)
        self.assertEqual(meal_from_db.name, 'Chicken Salad')
        self.assertEqual(meal_from_db.calories, 250)
        self.assertEqual(meal_from_db.protein, 30)
        self.assertEqual(meal_from_db.carbs, 15)
        self.assertEqual(meal_from_db.fat, 10)



class RecipeSerializerTestCase(APITestCase):

    def setUp(self):
        """
        Create a valid Meal instance for testing.
        """
        self.valid_meal = Meal.objects.create(
            name='Chicken Salad',
            description='A healthy chicken salad',
            calories=250,
            protein=30,
            carbs=15,
            fat=10
        )

        self.valid_recipe_data = {
            'meal': self.valid_meal.id,  # Pass meal ID instead of full meal data
            'instructions': 'Mix ingredients together.',
            'ingredients': 'Chicken, lettuce, olive oil'
        }

        self.invalid_recipe_data = {
            'meal': self.valid_meal.id,  # Pass meal ID instead of full meal data
            'instructions': 'A' * 501,  # Instructions exceed 500 characters
            'ingredients': 'B' * 501  # Ingredients exceed 500 characters
        }


    def test_recipe_serializer_valid_data(self):
        """
        Test that the RecipeSerializer works with valid data.
        """
        serializer = RecipeSerializer(data=self.valid_recipe_data)
    
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        self.assertEqual(serializer.validated_data['meal'], self.valid_meal)  # Check that the meal is the correct Meal instance
        self.assertEqual(serializer.validated_data['instructions'], 'Mix ingredients together.')
        self.assertEqual(serializer.validated_data['ingredients'], 'Chicken, lettuce, olive oil')


    def test_recipe_serializer_invalid_instructions_length(self):
        """
        Test that the RecipeSerializer raises a validation error for instructions length exceeding 500 characters.
        """
        invalid_data = self.invalid_recipe_data.copy()
        invalid_data['instructions'] = 'A' * 501  # Instructions exceed the max length
        serializer = RecipeSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Expecting validation error for instructions length


    def test_recipe_serializer_invalid_ingredients_length(self):
        """
        Test that the RecipeSerializer raises a validation error for ingredients length exceeding 500 characters.
        """
        invalid_data = self.invalid_recipe_data.copy()
        invalid_data['ingredients'] = 'B' * 501  # Ingredients exceed the max length
        serializer = RecipeSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Expecting validation error for ingredients length


    def test_recipe_serializer_missing_meal_data(self):
        """
        Test that the RecipeSerializer raises a validation error if meal data is missing.
        """
        invalid_data = self.valid_recipe_data.copy()
        del invalid_data['meal']  # Remove 'meal' to simulate missing data
        serializer = RecipeSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for missing 'meal'


    def test_recipe_serializer_create(self):
        """
        Test that the RecipeSerializer correctly creates a new Recipe instance with nested meal data.
        """
        serializer = RecipeSerializer(data=self.valid_recipe_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        recipe_instance = serializer.save()  # Save the new recipe instance
        
        # Fetch the recipe instance from the database and assert its fields
        recipe_from_db = Recipe.objects.get(id=recipe_instance.id)
        self.assertEqual(recipe_from_db.meal.name, 'Chicken Salad')
        self.assertEqual(recipe_from_db.instructions, 'Mix ingredients together.')
        self.assertEqual(recipe_from_db.ingredients, 'Chicken, lettuce, olive oil')


    def test_recipe_serializer_create_invalid_meal_data(self):
        """
        Test that the RecipeSerializer raises a validation error if meal data is invalid.
        """
        invalid_data = self.valid_recipe_data.copy()
        invalid_data['meal'] = 'invalid_id'  # Invalid meal ID (string instead of integer)
        serializer = RecipeSerializer(data=invalid_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)  # Should raise validation error for invalid meal ID


class MealPlanSerializerTestCase(APITestCase):

    def setUp(self):
        """
        Create sample CustomUser, Meal, and MealPlan instances for testing.
        """
        # Create a CustomUser instance
        self.user = CustomUser.objects.create_user(
            email='user@mail.com',
            username='testuser',
            password='userpassword'
        )

        # Create some Meal instances
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            description="A healthy chicken salad",
            calories=250,
            protein=30,
            carbs=15,
            fat=10
        )
        self.meal_2 = Meal.objects.create(
            name="Vegetable Stir-fry",
            description="A healthy vegetable stir-fry",
            calories=200,
            protein=10,
            carbs=40,
            fat=5
        )

        # Create a MealPlan instance
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name="Weekly Plan",
            description="A meal plan for the week"
        )

        # Add meals to the meal plan (use set() for many-to-many field)
        self.meal_plan.meals.set([self.meal_1, self.meal_2])

        # Prepare valid and invalid test data
        self.valid_data = {
            'user': self.user.id,
            'name': 'Weekly Meal Plan',
            'description': 'A meal plan with healthy meals',
            'meals': [self.meal_1.id, self.meal_2.id],  # Pass meal IDs
        }

        self.invalid_data = {
            'user': self.user.id,
            'name': '',  # Invalid name (empty string)
            'description': 'Invalid data test',
            'meals': [self.meal_1.id],  # Only one meal
        }


    def test_meal_plan_serializer_valid_data(self):
        """
        Test that the MealPlanSerializer works with valid data, including nested meals.
        """
        serializer = MealPlanSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        meal_plan = serializer.save()

        # Check if MealPlan was created with correct data
        self.assertEqual(meal_plan.name, 'Weekly Meal Plan')
        self.assertEqual(meal_plan.description, 'A meal plan with healthy meals')
        self.assertEqual(meal_plan.user, self.user)
        self.assertEqual(meal_plan.meals.count(), 2)  # Check if both meals were added


    def test_meal_plan_serializer_invalid_data(self):
        """
        Test that the MealPlanSerializer raises validation error with invalid data.
        """
        serializer = MealPlanSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())  # Ensure serializer is not valid
        self.assertIn('name', serializer.errors)  # Ensure 'name' field has validation errors


    def test_create_meal_plan(self):
        """
        Test that the `create()` method of MealPlanSerializer works as expected.
        """
        serializer = MealPlanSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        meal_plan = serializer.save()

        # Ensure the meal_plan is saved with the correct meals
        self.assertEqual(meal_plan.name, 'Weekly Meal Plan')
        self.assertEqual(meal_plan.description, 'A meal plan with healthy meals')
        self.assertEqual(meal_plan.user, self.user)
        self.assertEqual(meal_plan.meals.count(), 2)  # Two meals in the plan


    def test_update_meal_plan(self):
        """
        Test that the `update()` method of MealPlanSerializer works as expected.
        """
        updated_data = {
            'user': self.user.id,  # Make sure the user is included
            'name': 'Updated Meal Plan',
            'description': 'Updated description for meal plan',
            'meals': [self.meal_2.id],  # Only include meal_2 for this update
        }

        serializer = MealPlanSerializer(instance=self.meal_plan, data=updated_data)
        
        if not serializer.is_valid():
            print(serializer.errors)  # Print the validation errors for debugging
        
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        updated_meal_plan = serializer.save()

        # Ensure the meal plan was updated
        self.assertEqual(updated_meal_plan.name, 'Updated Meal Plan')
        self.assertEqual(updated_meal_plan.description, 'Updated description for meal plan')
        self.assertEqual(updated_meal_plan.meals.count(), 1)  # Only meal_2 is included now
        

    def test_meal_plan_relationship_with_meals(self):
        """
        Test that the relationship between MealPlan and Meals is handled properly.
        """
        # Create a new MealPlan with meals
        new_meal_plan_data = {
            'user': self.user.id,
            'name': 'Test Meal Plan',
            'description': 'Test meal plan description',
            'meals': [self.meal_1.id, self.meal_2.id],
        }

        serializer = MealPlanSerializer(data=new_meal_plan_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        new_meal_plan = serializer.save()

        # Check if meals are correctly linked
        self.assertEqual(new_meal_plan.meals.count(), 2)  # Check if both meals were added


    def test_invalid_meal_plan_meals(self):
        """
        Test that the MealPlanSerializer raises a validation error when meals are empty.
        """
        invalid_meal_plan_data = {
            'user': self.user.id,
            'name': 'Invalid Meal Plan',
            'description': 'Test invalid meal plan',
            'meals': []  # No meals provided
        }

        serializer = MealPlanSerializer(data=invalid_meal_plan_data)
        self.assertFalse(serializer.is_valid())  # Ensure serializer is not valid
        self.assertIn('meals', serializer.errors)  # Ensure 'meals' field has validation errors
        self.assertEqual(str(serializer.errors['meals'][0]), 'At least one meal must be provided.')


    def test_meal_plan_name_max_length(self):
        """
        Test that the meal plan name does not exceed max length.
        """
        long_name = 'A' * 256  # Name longer than the max length of 255
        invalid_data = {
            'user': self.user.id,
            'name': long_name,
            'description': 'Test invalid meal plan',
            'meals': [self.meal_1.id],
        }

        serializer = MealPlanSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())  # Ensure serializer is not valid
        self.assertIn('name', serializer.errors)  # Ensure the 'name' field has a validation error


    def test_meal_plan_description_default(self):
        """
        Test that the default description is set if no description is provided.
        """
        new_meal_plan_data = {
            'user': self.user.id,
            'name': 'Test Meal Plan without Description',
            'meals': [self.meal_1.id]
        }

        serializer = MealPlanSerializer(data=new_meal_plan_data)
        self.assertTrue(serializer.is_valid())  # Ensure serializer is valid
        meal_plan = serializer.save()

        # Ensure default description is used
        self.assertEqual(meal_plan.description, 'No description provided.')  # Default description
