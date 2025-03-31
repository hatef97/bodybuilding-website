from django.test import TestCase
from django.core.exceptions import ValidationError

from core.models import CustomUser as User
from nutrition.models import *



class CalorieCalculatorTestCase(TestCase):
    
    def setUp(self):
        """
        Create a valid instance of the CalorieCalculator for tests
        """
        self.calculator = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75,
            height=175,
            activity_level='moderate_activity'
        )


    def test_calorie_calculation_male(self):
        """
        Test the calorie calculation for male with moderate activity.
        """
        # Using Harris-Benedict formula:
        # BMR = 10 * weight + 6.25 * height - 5 * age + 5 (for male)
        expected_bmr = 10 * self.calculator.weight + 6.25 * self.calculator.height - 5 * self.calculator.age + 5
        # BMR for moderate activity is multiplied by 1.55
        expected_calories = expected_bmr * 1.55

        self.assertEqual(self.calculator.calculate_calories(), expected_calories)


    def test_calorie_calculation_female(self):
        """
        Test the calorie calculation for female with moderate activity.
        """
        # Create a female instance
        female_calculator = CalorieCalculator.objects.create(
            gender='female',
            age=30,
            weight=75,
            height=175,
            activity_level='moderate_activity'
        )
        
        # Using Harris-Benedict formula:
        # BMR = 10 * weight + 6.25 * height - 5 * age - 161 (for female)
        expected_bmr = 10 * female_calculator.weight + 6.25 * female_calculator.height - 5 * female_calculator.age - 161
        # BMR for moderate activity is multiplied by 1.55
        expected_calories = expected_bmr * 1.55

        self.assertEqual(female_calculator.calculate_calories(), expected_calories)


    def test_invalid_gender(self):
        """
        Test invalid gender input should raise a ValidationError
        """
        self.calculator.gender = 'other'
        with self.assertRaises(ValidationError):
            self.calculator.clean()  # This should raise a validation error


    def test_invalid_activity_level(self):
        """
        Test invalid activity level input should raise a ValidationError
        """
        self.calculator.activity_level = 'extreme'
        with self.assertRaises(ValidationError):
            self.calculator.clean()


    def test_negative_age(self):
        """
        Test invalid negative age value should raise a ValidationError
        """
        self.calculator.age = -1
        with self.assertRaises(ValidationError):
            self.calculator.clean()


    def test_negative_weight(self):
        """
        Test invalid negative weight value should raise a ValidationError
        """
        self.calculator.weight = -1
        with self.assertRaises(ValidationError):
            self.calculator.clean()

    def test_negative_height(self):
        """
        Test invalid negative height value should raise a ValidationError
        """
        self.calculator.height = -1
        with self.assertRaises(ValidationError):
            self.calculator.clean()


    def test_valid_calculator_creation(self):
        """
        Test valid creation of a CalorieCalculator instance.
        """
        self.assertEqual(self.calculator.gender, 'male')
        self.assertEqual(self.calculator.age, 30)
        self.assertEqual(self.calculator.weight, 75)
        self.assertEqual(self.calculator.height, 175)
        self.assertEqual(self.calculator.activity_level, 'moderate_activity')


    def test_calories_for_sedentary(self):
        """
        Test calorie calculation for sedentary activity level
        """
        sedentary_calculator = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75,
            height=175,
            activity_level='sedentary'
        )
        
        # Calculate BMR first
        expected_bmr = 10 * sedentary_calculator.weight + 6.25 * sedentary_calculator.height - 5 * sedentary_calculator.age + 5
        # For sedentary activity, BMR is multiplied by 1.2
        expected_calories = expected_bmr * 1.2

        self.assertEqual(sedentary_calculator.calculate_calories(), expected_calories)


    def test_calories_for_light_activity(self):
        """
        Test calorie calculation for light activity level
        """
        light_activity_calculator = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75,
            height=175,
            activity_level='light_activity'
        )
        
        # Calculate BMR first
        expected_bmr = 10 * light_activity_calculator.weight + 6.25 * light_activity_calculator.height - 5 * light_activity_calculator.age + 5
        # For light activity, BMR is multiplied by 1.375
        expected_calories = expected_bmr * 1.375

        self.assertEqual(light_activity_calculator.calculate_calories(), expected_calories)


    def test_calories_for_heavy_activity(self):
        """
        Test calorie calculation for heavy activity level
        """
        heavy_activity_calculator = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75,
            height=175,
            activity_level='heavy_activity'
        )
        
        # Calculate BMR first
        expected_bmr = 10 * heavy_activity_calculator.weight + 6.25 * heavy_activity_calculator.height - 5 * heavy_activity_calculator.age + 5
        # For heavy activity, BMR is multiplied by 1.725
        expected_calories = expected_bmr * 1.725

        self.assertEqual(heavy_activity_calculator.calculate_calories(), expected_calories)


    def test_create_calorie_calculator_with_invalid_gender(self):
        """
        Test creation of CalorieCalculator with invalid gender
        """
        invalid_gender_calculator = CalorieCalculator(
            gender='unknown',  # Invalid gender
            age=30,
            weight=75,
            height=175,
            activity_level='moderate_activity'
        )
        with self.assertRaises(ValidationError):
            invalid_gender_calculator.clean()


    def test_create_calorie_calculator_with_invalid_activity_level(self):
        """
        Test creation of CalorieCalculator with invalid activity level
        """
        invalid_activity_level_calculator = CalorieCalculator(
            gender='male',
            age=30,
            weight=75,
            height=175,
            activity_level='unknown'
        )
        with self.assertRaises(ValidationError):
            invalid_activity_level_calculator.clean()


    def test_str_method(self):
        """
        Test the string representation of the CalorieCalculator model.
        """
        self.assertEqual(str(self.calculator), "Calorie Calculation for male (30 years)")



class MealTestCase(TestCase):

    def setUp(self):
        """
        Create a valid instance of the Meal model for tests.
        """
        self.meal = Meal.objects.create(
            name="Chicken Salad",
            description="A healthy chicken salad",
            calories=250,
            protein=30,
            carbs=15,
            fat=10
        )


    def test_meal_creation(self):
        """Test the creation of a Meal instance."""
        self.assertEqual(self.meal.name, "Chicken Salad")
        self.assertEqual(self.meal.description, "A healthy chicken salad")
        self.assertEqual(self.meal.calories, 250)
        self.assertEqual(self.meal.protein, 30)
        self.assertEqual(self.meal.carbs, 15)
        self.assertEqual(self.meal.fat, 10)


    def test_meal_default_description(self):
        """Test that a meal created without a description has the default description."""
        meal_without_description = Meal.objects.create(
            name="Rice",
            calories=200,
            protein=5,
            carbs=40,
            fat=1
        )
        self.assertEqual(meal_without_description.description, "No description provided.")


    def test_invalid_calories(self):
        """Test that invalid (negative) values for calories raise a validation error."""
        with self.assertRaises(ValidationError):
            meal_invalid_calories = Meal(name="Invalid Meal", calories=-100, protein=10, carbs=20, fat=5)
            meal_invalid_calories.full_clean()  # This should raise a validation error for negative calories


    def test_invalid_protein(self):
        """Test that invalid (negative) values for protein raise a validation error."""
        with self.assertRaises(ValidationError):
            meal_invalid_protein = Meal(name="Invalid Meal", calories=200, protein=-10, carbs=20, fat=5)
            meal_invalid_protein.full_clean()  # This should raise a validation error for negative protein


    def test_invalid_carbs(self):
        """Test that invalid (negative) values for carbs raise a validation error."""
        with self.assertRaises(ValidationError):
            meal_invalid_carbs = Meal(name="Invalid Meal", calories=200, protein=10, carbs=-20, fat=5)
            meal_invalid_carbs.full_clean()  # This should raise a validation error for negative carbs


    def test_invalid_fat(self):
        """Test that invalid (negative) values for fat raise a validation error."""
        with self.assertRaises(ValidationError):
            meal_invalid_fat = Meal(name="Invalid Meal", calories=200, protein=10, carbs=20, fat=-5)
            meal_invalid_fat.full_clean()  # This should raise a validation error for negative fat


    def test_meal_string_representation(self):
        """Test the string representation of the Meal model."""
        self.assertEqual(str(self.meal), "Chicken Salad")


    def test_calories_validation(self):
        """Test that a Meal with zero calories should raise a validation error."""
        meal_with_zero_calories = Meal(name="Zero Calorie Meal", calories=0, protein=5, carbs=10, fat=2)
        with self.assertRaises(ValidationError):
            meal_with_zero_calories.full_clean()  # This should raise a validation error for zero calories


    def test_meal_name_length(self):
        """Test that the meal name length does not exceed the maximum allowed length."""
        long_name = "A" * 256  # Name exceeding max length
        meal_with_long_name = Meal(name=long_name, description="Long name test", calories=200, protein=10, carbs=20, fat=5)
        with self.assertRaises(ValidationError):
            meal_with_long_name.full_clean()  # This should raise a validation error due to name length


    def test_save_meal(self):
        """Test saving a valid Meal instance to the database."""
        meal = Meal(name="Salmon", description="Grilled salmon with veggies", calories=300, protein=25, carbs=10, fat=15)
        meal.save()
        saved_meal = Meal.objects.get(id=meal.id)
        self.assertEqual(saved_meal.name, "Salmon")
        self.assertEqual(saved_meal.description, "Grilled salmon with veggies")
        self.assertEqual(saved_meal.calories, 300)
        self.assertEqual(saved_meal.protein, 25)
        self.assertEqual(saved_meal.carbs, 10)
        self.assertEqual(saved_meal.fat, 15)


    def test_meal_calories_default(self):
        """Test that the default calories value is correctly set when not provided."""
        meal_without_calories = Meal.objects.create(
            name="Tofu Stir-Fry",
            description="A delicious vegetarian stir-fry",
            protein=20,
            carbs=30,
            fat=10
        )
        self.assertEqual(meal_without_calories.calories, 0)  # Default should be 0


    def test_meal_fat_default(self):
        """Test that the default fat value is correctly set when not provided."""
        meal_without_fat = Meal.objects.create(
            name="Vegetable Soup",
            description="A healthy vegetable soup",
            calories=150,
            protein=5,
            carbs=20
        )
        self.assertEqual(meal_without_fat.fat, 0)  # Default should be 0



class RecipeTestCase(TestCase):

    def setUp(self):
        """
        Create valid instances of Meal and Recipe models for testing.
        """
        # Create a Meal instance that will be used in the Recipe
        self.meal = Meal.objects.create(
            name="Chicken Salad",
            description="A healthy chicken salad",
            calories=250,
            protein=30,
            carbs=15,
            fat=10
        )
        
        # Create a Recipe instance associated with the Meal
        self.recipe = Recipe.objects.create(
            meal=self.meal,
            instructions="Mix ingredients together.",
            ingredients="Chicken, lettuce, olive oil"
        )


    def test_recipe_creation(self):
        """
        Test the creation of a Recipe instance and verify all fields.
        """
        self.assertEqual(self.recipe.meal.name, "Chicken Salad")
        self.assertEqual(self.recipe.instructions, "Mix ingredients together.")
        self.assertEqual(self.recipe.ingredients, "Chicken, lettuce, olive oil")


    def test_recipe_string_representation(self):
        """
        Test the string representation of the Recipe model.
        """
        self.assertEqual(str(self.recipe), "Recipe for Chicken Salad")


    def test_recipe_meal_relationship(self):
        """
        Test the relationship between Recipe and Meal.
        """
        meal_in_recipe = self.recipe.meal
        self.assertEqual(meal_in_recipe.name, "Chicken Salad")  # The meal should be correctly linked
        self.assertTrue(self.recipe.meal.recipes.filter(id=self.recipe.id).exists())  # Ensure reverse relationship works


    def test_missing_meal(self):
        """
        Test that a Recipe cannot be created without a related Meal.
        """
        with self.assertRaises(ValidationError):
            recipe_without_meal = Recipe(
                meal=None,
                instructions="Instructions here",
                ingredients="Ingredients here"
            )
            recipe_without_meal.full_clean()  # This should raise a ValidationError because 'meal' is required.


    def test_recipe_instructions_length(self):
        """
        Test that the length of the instructions is reasonable and doesn't exceed a maximum length (e.g., 500).
        """
        long_instructions = "A" * 501  # Exceeding max length
        recipe_with_long_instructions = Recipe(
            meal=self.meal,
            instructions=long_instructions,
            ingredients="Chicken, lettuce, olive oil"
        )
        with self.assertRaises(ValidationError):
            recipe_with_long_instructions.full_clean()  # This should raise a validation error due to instruction length


    def test_recipe_ingredients_length(self):
        """
        Test that the length of ingredients is reasonable and doesn't exceed a maximum length (e.g., 500).
        """
        long_ingredients = "A" * 501  # Exceeding max length
        recipe_with_long_ingredients = Recipe(
            meal=self.meal,
            instructions="Instructions here",
            ingredients=long_ingredients
        )
        with self.assertRaises(ValidationError):
            recipe_with_long_ingredients.full_clean()  # This should raise a validation error due to ingredient length


    def test_recipe_save(self):
        """
        Test saving a valid Recipe instance to the database and ensuring it can be retrieved.
        """
        saved_recipe = Recipe.objects.get(id=self.recipe.id)
        self.assertEqual(saved_recipe.meal.name, "Chicken Salad")
        self.assertEqual(saved_recipe.instructions, "Mix ingredients together.")
        self.assertEqual(saved_recipe.ingredients, "Chicken, lettuce, olive oil")


    def test_reverse_recipe_lookup(self):
        """
        Test that we can retrieve recipes related to a meal.
        """
        # Create another recipe linked to the same meal
        another_recipe = Recipe.objects.create(
            meal=self.meal,
            instructions="Grill chicken and serve.",
            ingredients="Chicken, salt, pepper"
        )
        # Check if we can retrieve both recipes through the meal's related name 'recipes'
        recipes_for_meal = self.meal.recipes.all()
        self.assertEqual(recipes_for_meal.count(), 2)  # Should return 2 recipes
        self.assertTrue(another_recipe in recipes_for_meal)  # The new recipe should be in the result



class MealPlanTestCase(TestCase):

    def setUp(self):
        """
        Create valid instances of Meal, MealPlan, and a CustomUser for testing.
        """
        # Create a CustomUser instance
        self.user = User.objects.create_user(
            email='user@mail.com',
            username='admin1',
            password='userpassword'
        )
        
        # Create Meal instances to associate with the MealPlan
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

        # Create a MealPlan instance associated with the CustomUser and Meals
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name="Weekly Plan",
            description="A plan with healthy meals"
        )

        # Add meals to the MealPlan using the many-to-many relationship
        self.meal_plan.meals.set([self.meal_1, self.meal_2])

    def test_meal_plan_creation(self):
        """
        Test the creation of a MealPlan instance and verify all fields.
        """
        self.assertEqual(self.meal_plan.name, "Weekly Plan")
        self.assertEqual(self.meal_plan.user.username, "admin1")
        self.assertEqual(self.meal_plan.description, "A plan with healthy meals")
        self.assertEqual(self.meal_plan.meals.count(), 2)  # Two meals should be associated with the plan

    def test_meal_plan_string_representation(self):
        """
        Test the string representation of the MealPlan model.
        """
        self.assertEqual(str(self.meal_plan), "Weekly Plan")

    def test_meal_plan_user_relationship(self):
        """
        Test the relationship between MealPlan and CustomUser.
        """
        meal_plan_user = self.meal_plan.user
        self.assertEqual(meal_plan_user.username, "admin1")  # The user should be correctly linked
        self.assertTrue(self.user.meal_plans_user.filter(id=self.meal_plan.id).exists())  # Ensure reverse relationship works

    def test_missing_user(self):
        """
        Test that a MealPlan cannot be created without a related user.
        """
        with self.assertRaises(ValidationError):
            meal_plan_without_user = MealPlan(
                user=None,
                name="Invalid Plan",
                description="This plan has no user"
            )
            meal_plan_without_user.full_clean()  # This should raise a validation error because 'user' is required.

    def test_meal_plan_name_length(self):
        """
        Test that the name length of the MealPlan does not exceed the maximum allowed length.
        """
        long_name = "A" * 256  # Exceeding max length (255 characters)
        meal_plan_with_long_name = MealPlan(
            user=self.user,
            name=long_name,
            description="A long name test",
        )
        with self.assertRaises(ValidationError):
            meal_plan_with_long_name.full_clean()  # This should raise a validation error due to name length

    def test_add_meal_to_meal_plan(self):
        """
        Test adding a meal to a MealPlan and ensure the relationship works.
        """
        new_meal = Meal.objects.create(
            name="Tofu Stir-Fry",
            description="A delicious vegetarian stir-fry",
            calories=300,
            protein=20,
            carbs=25,
            fat=12
        )
        
        # Add the new meal to the meal plan
        self.meal_plan.meals.add(new_meal)

        # Check if the meal is correctly associated with the plan
        self.assertEqual(self.meal_plan.meals.count(), 3)  # The meal plan should have 3 meals now

    def test_reverse_meal_plan_lookup(self):
        """
        Test reverse lookup from a user to their associated MealPlans.
        """
        meal_plans_for_user = self.user.meal_plans_user.all()
        self.assertEqual(meal_plans_for_user.count(), 1)  # There should be only 1 MealPlan for the user
        self.assertTrue(self.meal_plan in meal_plans_for_user)  # The created MealPlan should be in the user's MealPlans

    def test_remove_meal_from_meal_plan(self):
        """
        Test removing a meal from a MealPlan.
        """
        new_meal = Meal.objects.create(
            name="Tofu Stir-Fry",
            description="A delicious vegetarian stir-fry",
            calories=300,
            protein=20,
            carbs=25,
            fat=12
        )
        
        # Add the new meal to the meal plan
        self.meal_plan.meals.add(new_meal)
        
        # Remove the meal from the plan
        self.meal_plan.meals.remove(new_meal)

        # Ensure the meal has been removed from the meal plan
        self.assertEqual(self.meal_plan.meals.count(), 2)  # Only two meals should remain in the plan

    def test_meal_plan_description_default(self):
        """
        Test that the default description value is correctly set when not provided.
        """
        meal_plan_without_description = MealPlan.objects.create(
            user=self.user,
            name="Simple Plan"
        )
        self.assertEqual(meal_plan_without_description.description, "No description provided.")  # Default should be set

    def test_meal_plan_save(self):
        """
        Test saving a valid MealPlan instance to the database.
        """
        saved_meal_plan = MealPlan.objects.get(id=self.meal_plan.id)
        self.assertEqual(saved_meal_plan.name, "Weekly Plan")
        self.assertEqual(saved_meal_plan.description, "A plan with healthy meals")
        self.assertEqual(saved_meal_plan.user.username, "admin1")
        self.assertEqual(saved_meal_plan.meals.count(), 2)  # Ensure the meals are saved with the plan
