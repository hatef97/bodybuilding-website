from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from nutrition.models import Meal, MealPlan, MealInMealPlan, Recipe, CalorieCalculator



class MealModelTests(TestCase):

    def setUp(self):
        self.valid_data = {
            "name": "Grilled Chicken Salad",
            "calories": 450,
            "protein": Decimal("35.5"),
            "carbs": Decimal("20.25"),
            "fats": Decimal("15.00"),
            "description": "A healthy meal with grilled chicken, lettuce, and vinaigrette."
        }


    def test_meal_creation_success(self):
        """
        Test creating a Meal with valid data.
        """
        meal = Meal.objects.create(**self.valid_data)
        self.assertEqual(meal.name, "Grilled Chicken Salad")
        self.assertEqual(meal.calories, 450)
        self.assertEqual(meal.protein, Decimal("35.5"))
        self.assertEqual(meal.carbs, Decimal("20.25"))
        self.assertEqual(meal.fats, Decimal("15.00"))
        self.assertEqual(str(meal), "Grilled Chicken Salad")


    def test_meal_string_representation(self):
        """
        Test that __str__ returns the name of the meal.
        """
        meal = Meal.objects.create(**self.valid_data)
        self.assertEqual(str(meal), meal.name)


    def test_meal_description_optional(self):
        """
        Test creating a meal without a description.
        """
        self.valid_data.pop("description")
        meal = Meal.objects.create(**self.valid_data)
        self.assertEqual(meal.description, None)


    def test_negative_calories_rejected(self):
        """
        Negative calories should raise an error.
        """
        self.valid_data["calories"] = -100
        with self.assertRaises(Exception):
            Meal.objects.create(**self.valid_data)


    def test_negative_macronutrients_rejected(self):
        """
        Negative protein/carbs/fats should raise an error.
        """
        fields = ["protein", "carbs", "fats"]
        for field in fields:
            data = {
                "name": "Test Meal",
                "calories": 500,
                "protein": Decimal("10.5"),
                "carbs": Decimal("20.5"),
                "fats": Decimal("10.0"),
                "description": "Test meal description"
            }
            data[field] = Decimal("-5.0")  # Set negative value for each field
            meal = Meal(**data)
            with self.assertRaises(ValidationError, msg=f"{field} should not accept negative values"):
                meal.clean() 


    def test_verbose_name_meta(self):
        """
        Test model Meta options for verbose_name and verbose_name_plural.
        """
        self.assertEqual(Meal._meta.verbose_name, "Meal")
        self.assertEqual(Meal._meta.verbose_name_plural, "Meals")



class MealPlanModelTests(TestCase):

    def setUp(self):
        """
        Set up the initial data for tests.
        """
        # Create some sample meals
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
        # Create a Meal Plan with these meals
        self.meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",
            goal="bulking"
        )
        # Add meals to the plan with 'order' specified
        MealInMealPlan.objects.create(meal=self.meal_1, meal_plan=self.meal_plan, order=1)
        MealInMealPlan.objects.create(meal=self.meal_2, meal_plan=self.meal_plan, order=2)


    def test_meal_plan_str(self):
        """
        Test the string representation of the MealPlan model.
        """
        self.assertEqual(str(self.meal_plan), "Bulking Meal Plan (Bulking)")


    def test_total_calories(self):
        """
        Test that total calories calculation is correct for the Meal Plan.
        """
        total_calories = self.meal_plan.total_calories()
        self.assertEqual(total_calories, 400 + 500)  # 400 from meal_1 + 500 from meal_2


    def test_total_protein(self):
        """
        Test that total protein calculation is correct for the Meal Plan.
        """
        total_protein = self.meal_plan.total_protein()
        self.assertEqual(total_protein, 35 + 40)  # 35 from meal_1 + 40 from meal_2


    def test_total_carbs(self):
        """
        Test that total carbs calculation is correct for the Meal Plan.
        """
        total_carbs = self.meal_plan.total_carbs()
        self.assertEqual(total_carbs, 10 + 5)  # 10 from meal_1 + 5 from meal_2


    def test_total_fats(self):
        """
        Test that total fats calculation is correct for the Meal Plan.
        """
        total_fats = self.meal_plan.total_fats()
        self.assertEqual(total_fats, 15 + 25)  # 15 from meal_1 + 25 from meal_2


    def test_goal_choices(self):
        """
        Test the available goal choices for the Meal Plan.
        """
        valid_goals = ['bulking', 'cutting', 'maintenance']
        for goal in valid_goals:
            meal_plan = MealPlan.objects.create(name=f"{goal.capitalize()} Plan", goal=goal)
            self.assertEqual(meal_plan.goal, goal)


    def test_goal_display(self):
        """
        Test the get_goal_display method for Meal Plan.
        """
        self.assertEqual(self.meal_plan.get_goal_display(), "Bulking")


    def test_meal_plan_empty_meal_list(self):
        """
        Test Meal Plan when no meals are added. Should return 0 for all nutritional values.
        """
        empty_meal_plan = MealPlan.objects.create(
            name="Empty Meal Plan",
            goal="cutting"
        )
        self.assertEqual(empty_meal_plan.total_calories(), 0)
        self.assertEqual(empty_meal_plan.total_protein(), 0)
        self.assertEqual(empty_meal_plan.total_carbs(), 0)
        self.assertEqual(empty_meal_plan.total_fats(), 0)


    def test_meal_plan_add_meal(self):
        """
        Test adding a new meal to the Meal Plan and recalculating total values.
        """
        # Add meals to the meal plan, specifying order
        self.meal_plan.meals.add(self.meal_1, through_defaults={'order': 1})
        self.meal_plan.meals.add(self.meal_2, through_defaults={'order': 2})
        
        # Ensure the total calories, protein, carbs, and fats are calculated correctly
        self.assertEqual(self.meal_plan.total_calories(), 500 + 400)  # Total calories should be sum of meal calories
        self.assertEqual(self.meal_plan.total_protein(), Decimal('35.00') + Decimal('40.00'))  # Total protein should be sum of protein content
        self.assertEqual(self.meal_plan.total_carbs(), Decimal('10.00') + Decimal('5.00'))  # Total carbs should be sum of carbs content
        self.assertEqual(self.meal_plan.total_fats(), Decimal('15.00') + Decimal('25.00'))  # Total fats should be sum of fat content


    def test_meal_plan_remove_meal(self):
        """
        Test removing a meal from the Meal Plan and recalculating total values.
        """
        self.meal_plan.meals.remove(self.meal_2)  # Remove the second meal (Grilled Salmon)
        
        # Recalculate totals after removing the meal
        self.assertEqual(self.meal_plan.total_calories(), 400)  # Only meal_1 remains
        self.assertEqual(self.meal_plan.total_protein(), 35)
        self.assertEqual(self.meal_plan.total_carbs(), 10)
        self.assertEqual(self.meal_plan.total_fats(), 15)


    def test_meal_plan_unique_name(self):
        """
        Test that meal plans with the same name can exist if the goal is different.
        """
        new_meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",  # Same name as the existing plan
            goal="cutting"  # Different goal, so should be allowed
        )
        self.assertEqual(new_meal_plan.name, "Bulking Meal Plan")
        self.assertEqual(new_meal_plan.goal, "cutting")


    def test_invalid_goal(self):
        """
        Test that providing an invalid goal value raises an error.
        """
        invalid_goal = "invalid_goal"  # This goal is not in the defined choices

        # Create a MealPlan instance without saving it to the database
        meal_plan = MealPlan(name="Invalid Goal Plan", goal=invalid_goal)

        # Try to call full_clean to trigger validation
        with self.assertRaises(ValidationError):
            meal_plan.full_clean() 



class MealInMealPlanModelTests(TestCase):

    def setUp(self):
        """
        Set up initial test data for MealInMealPlan.
        """
        # Create some sample meals
        self.meal_1 = Meal.objects.create(
            name="Chicken Salad",
            calories=400,
            protein=Decimal('35.00'),
            carbs=Decimal('10.00'),
            fats=Decimal('15.00'),
            description="A healthy chicken salad."
        )
        self.meal_2 = Meal.objects.create(
            name="Grilled Salmon",
            calories=500,
            protein=Decimal('40.00'),
            carbs=Decimal('5.00'),
            fats=Decimal('25.00'),
            description="Grilled salmon with vegetables."
        )
        # Create a Meal Plan
        self.meal_plan = MealPlan.objects.create(
            name="Bulking Meal Plan",
            goal="bulking"
        )


    def test_create_meal_in_meal_plan(self):
        """
        Test that a MealInMealPlan instance can be created correctly.
        """
        # Create the MealInMealPlan instance with an order
        meal_in_plan = MealInMealPlan.objects.create(
            meal_plan=self.meal_plan,
            meal=self.meal_1,
            order=1
        )

        # Check if the instance was created successfully
        self.assertEqual(meal_in_plan.meal_plan, self.meal_plan)
        self.assertEqual(meal_in_plan.meal, self.meal_1)
        self.assertEqual(meal_in_plan.order, 1)


    def test_ordering_of_meals_in_plan(self):
        """
        Test that the meals are ordered correctly in the meal plan.
        """
        # Create the MealInMealPlan instances
        meal_in_plan_1 = MealInMealPlan.objects.create(
            meal_plan=self.meal_plan,
            meal=self.meal_1,
            order=1
        )
        meal_in_plan_2 = MealInMealPlan.objects.create(
            meal_plan=self.meal_plan,
            meal=self.meal_2,
            order=2
        )

        # Retrieve the meal plan and check the order of meals
        meal_plan = MealPlan.objects.get(id=self.meal_plan.id)
        meal_in_meal_plan = meal_plan.meals.all().order_by('mealinmealplan__order')

        self.assertEqual(meal_in_meal_plan[0], self.meal_1)
        self.assertEqual(meal_in_meal_plan[1], self.meal_2)


    def test_unique_together_constraint(self):
        """
        Test that the same meal cannot be added twice to the same meal plan.
        """
        # Create the MealInMealPlan instance
        MealInMealPlan.objects.create(
            meal_plan=self.meal_plan,
            meal=self.meal_1,
            order=1
        )

        # Attempt to create the same meal in the same meal plan again
        with self.assertRaises(Exception):  # Should raise an IntegrityError due to unique_together constraint
            MealInMealPlan.objects.create(
                meal_plan=self.meal_plan,
                meal=self.meal_1,
                order=2
            )


    def test_str_method(self):
        """
        Test the string representation of the MealInMealPlan model.
        """
        # Create the MealInMealPlan instance
        meal_in_plan = MealInMealPlan.objects.create(
            meal_plan=self.meal_plan,
            meal=self.meal_1,
            order=1
        )

        # Check the string representation
        self.assertEqual(str(meal_in_plan), "Chicken Salad in Bulking Meal Plan")


    def test_meal_plan_total_calories_with_meals(self):
        """
        Test that adding meals to a plan updates the total calories correctly.
        """
        # Add meals to the meal plan
        self.meal_plan.meals.add(self.meal_1, through_defaults={'order': 1})
        self.meal_plan.meals.add(self.meal_2, through_defaults={'order': 2})

        # Check if the total calories are correctly calculated
        self.assertEqual(self.meal_plan.total_calories(), 400 + 500)  # Total calories should be sum of meal calories


    def test_meal_plan_total_macronutrients_with_meals(self):
        """
        Test that adding meals to a plan updates the total macronutrients correctly.
        """
        # Add meals to the meal plan
        self.meal_plan.meals.add(self.meal_1, through_defaults={'order': 1})
        self.meal_plan.meals.add(self.meal_2, through_defaults={'order': 2})

        # Check if the total macronutrients are correctly calculated
        self.assertEqual(self.meal_plan.total_protein(), Decimal('35.00') + Decimal('40.00'))
        self.assertEqual(self.meal_plan.total_carbs(), Decimal('10.00') + Decimal('5.00'))
        self.assertEqual(self.meal_plan.total_fats(), Decimal('15.00') + Decimal('25.00'))



class RecipeModelTests(TestCase):
    
    def setUp(self):
        """
        Set up initial test data for the Recipe model.
        """
        # Create a sample recipe
        self.recipe_1 = Recipe.objects.create(
            name="Chicken Stir Fry",
            ingredients="Chicken, Soy Sauce, Vegetables, Garlic, Ginger",
            instructions="Cook chicken, stir-fry with vegetables, add soy sauce.",
            calories=350,
            protein=25.50,
            carbs=30.00,
            fats=10.00
        )


    def test_create_recipe(self):
        """
        Test that a Recipe instance can be created with valid data.
        """
        recipe = self.recipe_1
        self.assertEqual(recipe.name, "Chicken Stir Fry")
        self.assertEqual(recipe.ingredients, "Chicken, Soy Sauce, Vegetables, Garlic, Ginger")
        self.assertEqual(recipe.instructions, "Cook chicken, stir-fry with vegetables, add soy sauce.")
        self.assertEqual(recipe.calories, 350)
        self.assertEqual(recipe.protein, Decimal('25.50'))
        self.assertEqual(recipe.carbs, Decimal('30.00'))
        self.assertEqual(recipe.fats, Decimal('10.00'))


    def test_str_method(self):
        """
        Test the string representation of the Recipe model.
        """
        recipe = self.recipe_1
        self.assertEqual(str(recipe), "Chicken Stir Fry")


    def test_positive_calories(self):
        """
        Test that calories should be positive.
        """
        recipe = Recipe(name="Test Recipe", ingredients="Test Ingredients", instructions="Test Instructions",
                        calories=500, protein=25.5, carbs=50.0, fats=15.0)
        recipe.save()
        self.assertGreater(recipe.calories, 0, "Calories must be a positive number.")


    def test_positive_protein(self):
        """
        Test that protein should be positive.
        """
        recipe = Recipe(name="Test Recipe", ingredients="Test Ingredients", instructions="Test Instructions",
                        calories=500, protein=20.0, carbs=50.0, fats=15.0)
        recipe.save()
        self.assertGreater(recipe.protein, 0, "Protein must be a positive number.")


    def test_positive_carbs(self):
        """
        Test that carbs should be positive.
        """
        recipe = Recipe(name="Test Recipe", ingredients="Test Ingredients", instructions="Test Instructions",
                        calories=500, protein=20.0, carbs=30.0, fats=15.0)
        recipe.save()
        self.assertGreater(recipe.carbs, 0, "Carbs must be a positive number.")


    def test_positive_fats(self):
        """
        Test that fats should be positive.
        """
        recipe = Recipe(name="Test Recipe", ingredients="Test Ingredients", instructions="Test Instructions",
                        calories=500, protein=20.0, carbs=30.0, fats=10.0)
        recipe.save()
        self.assertGreater(recipe.fats, 0, "Fats must be a positive number.")


    def test_invalid_negative_calories(self):
        """
        Test that negative calories raise an error.
        """
        recipe = Recipe(
            name="Test Invalid Recipe",
            ingredients="Test Ingredients",
            instructions="Test Instructions",
            calories=-1,  # Negative value
            protein=20.0,
            carbs=30.0,
            fats=10.0
        )
        with self.assertRaises(ValidationError):
            recipe.clean() 


    def test_invalid_negative_protein(self):
        """
        Test that negative protein raises an error.
        """
        recipe = Recipe(
            name="Test Invalid Recipe",
            ingredients="Test Ingredients",
            instructions="Test Instructions",
            calories=500,
            protein=-5.0,  # Negative value
            carbs=30.0,
            fats=10.0
        )
        with self.assertRaises(ValidationError):
            recipe.clean() 


    def test_invalid_negative_carbs(self):
        """
        Test that negative carbs raise an error.
        """
        recipe = Recipe(
            name="Test Invalid Recipe",
            ingredients="Test Ingredients",
            instructions="Test Instructions",
            calories=500,
            protein=20.0,
            carbs=-5.0,  # Negative value
            fats=10.0
        )
        with self.assertRaises(ValidationError):
            recipe.clean()


    def test_invalid_negative_fats(self):
    #     """
    #     Test that negative fats raise an error.
    #     """
        recipe = Recipe(
            name="Test Invalid Recipe",
            ingredients="Test Ingredients",
            instructions="Test Instructions",
            calories=500,
            protein=20.0,
            carbs=30.0,
            fats=-5.0  # Negative value
        )
        with self.assertRaises(ValidationError):
            recipe.clean() 



class CalorieCalculatorTests(TestCase):
    
    def setUp(self):
        """
        Set up test data for the CalorieCalculator model.
        """
        self.calculator_1 = CalorieCalculator.objects.create(
            gender='male',
            age=30,
            weight=75.0,
            height=175.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        self.calculator_2 = CalorieCalculator.objects.create(
            gender='female',
            age=25,
            weight=65.0,
            height=160.0,
            activity_level='light_activity',
            goal='gain'
        )
        self.calculator_3 = CalorieCalculator.objects.create(
            gender='male',
            age=45,
            weight=85.0,
            height=180.0,
            activity_level='sedentary',
            goal='lose'
        )


    def test_calories_for_male_moderate_activity(self):
        """
        Test if the caloric calculation works for a male with moderate activity level.
        """
        # Correct expected calculation
        expected_calories = 1698.75 * 1.55  # 1698.75 is the BMR for the given inputs
        
        # Assert that the calculated calories are correct
        self.assertEqual(self.calculator_1.calculate_calories(), expected_calories)


    def test_calories_for_female_light_activity(self):
        """
        Test if the caloric calculation works for a female with light activity level.
        """
        expected_calories = self.calculator_2.calculate_calories()
        self.assertEqual(expected_calories, (65.0 * 10 + 6.25 * 160.0 - 5 * 25 - 161) * 1.375)  # Expected formula for female BMR * activity multiplier


    def test_calories_for_male_sedentary(self):
        """
        Test if the caloric calculation works for a male with sedentary activity level.
        """
        expected_calories = self.calculator_3.calculate_calories()
        self.assertEqual(expected_calories, (85.0 * 10 + 6.25 * 180.0 - 5 * 45 + 5) * 1.2)  # Expected formula for male BMR * activity multiplier


    def test_calories_for_invalid_gender(self):
        """
        Test if an invalid gender raises an exception.
        """
        # Create a CalorieCalculator object with an invalid gender value
        calorie_calculator = CalorieCalculator(
            gender='invalid_gender',  # Invalid gender
            age=30,
            weight=75.0,
            height=175.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        
        # Check that the ValidationError is raised when we try to validate the object
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()


    def test_calories_for_invalid_activity_level(self):
        """
        Test if an invalid activity level raises an exception.
        """
        # Create a CalorieCalculator object with an invalid activity level
        calorie_calculator = CalorieCalculator(
            gender='male',
            age=30,
            weight=75.0,
            height=175.0,
            activity_level='invalid_activity',  # Invalid activity level
            goal='maintain'
        )
        
        # Check that the ValidationError is raised when we try to validate the object
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()


    def test_calories_for_invalid_goal(self):
        """
        Test if an invalid goal raises an exception.
        """
        # Creating an invalid goal, "build", which is not in the list of valid goals
        calorie_calculator = CalorieCalculator(
            gender='male',
            age=30,
            weight=75.0,
            height=175.0,
            activity_level='moderate_activity',
            goal='build'  # Invalid goal
        )
        
        # Check that the ValidationError is raised when we try to save the object
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()


    def test_calories_for_negative_values(self):
        """
        Test if negative values for weight, height, or age raise validation errors.
        """
        # Test negative age
        calorie_calculator = CalorieCalculator(
            gender='male',
            age=-30,
            weight=75.0,
            height=175.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()  # This should raise a ValidationError

        # Test negative weight
        calorie_calculator = CalorieCalculator(
            gender='male',
            age=30,
            weight=-75.0,
            height=175.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()  # This should raise a ValidationError

        # Test negative height
        calorie_calculator = CalorieCalculator(
            gender='male',
            age=30,
            weight=75.0,
            height=-175.0,
            activity_level='moderate_activity',
            goal='maintain'
        )
        with self.assertRaises(ValidationError):
            calorie_calculator.clean()  # This should raise a ValidationError


    def test_calorie_calculation_for_maintenance_goal(self):
        """
        Test if the correct number of calories are returned for a maintenance goal.
        """
        # Expected calculation for maintenance goal using Harris-Benedict formula:
        bmr = 10 * 75.0 + 6.25 * 175.0 - 5 * 30 + 5  # BMR for male = 10 * weight + 6.25 * height - 5 * age + 5
        maintenance_calories = bmr * 1.55  # BMR * activity factor for moderate activity

        # Check that the calculated calories match the expected value
        self.assertEqual(self.calculator_1.calculate_calories(), maintenance_calories)


    def test_calorie_calculation_for_gain_goal(self):
        """
        Test if the correct number of calories are returned for a gain goal.
        """
        # Expected BMR calculation for a female with the given weight, height, and age using the Harris-Benedict formula
        bmr = 10 * 65.0 + 6.25 * 160.0 - 5 * 25 - 161  # BMR for female = 10 * weight + 6.25 * height - 5 * age - 161
        gain_calories = bmr * 1.375  # BMR * activity factor for light activity (gain weight goal)

        # Check that the calculated calories match the expected value for the "gain" goal
        self.assertEqual(self.calculator_2.calculate_calories(), gain_calories)


    def test_calorie_calculation_for_lose_goal(self):
        """
        Test if the correct number of calories are returned for a lose goal.
        """
        # Expected BMR calculation for a male with the given weight, height, and age using the Harris-Benedict formula
        bmr = 10 * 85.0 + 6.25 * 180.0 - 5 * 45 + 5  # BMR for male = 10 * weight + 6.25 * height - 5 * age + 5
        lose_calories = bmr * 1.2  # BMR * activity factor for sedentary (lose weight goal)

        # Check that the calculated calories match the expected value for the "lose" goal
        self.assertEqual(self.calculator_3.calculate_calories(), lose_calories)


    def test_calorie_calculation_for_different_ages(self):
        """
        Test if calorie calculation adjusts for different ages.
        """
        calculator_4 = CalorieCalculator.objects.create(
            gender='female',
            age=50,
            weight=60.0,
            height=160.0,
            activity_level='light_activity',
            goal='maintain'
        )
        expected_calories = (60.0 * 10 + 6.25 * 160.0 - 5 * 50 - 161) * 1.375
        self.assertEqual(calculator_4.calculate_calories(), expected_calories)


    def test_calorie_calculation_for_different_heights(self):
        """
        Test if calorie calculation adjusts for different heights.
        """
        calculator_5 = CalorieCalculator.objects.create(
            gender='male',
            age=25,
            weight=70.0,
            height=190.0,  # Taller height
            activity_level='moderate_activity',
            goal='gain'
        )
        expected_calories = (70.0 * 10 + 6.25 * 190.0 - 5 * 25 + 5) * 1.55
        self.assertEqual(calculator_5.calculate_calories(), expected_calories)
