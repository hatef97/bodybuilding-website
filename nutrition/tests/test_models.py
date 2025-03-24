from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from nutrition.models import Meal, MealPlan, MealInMealPlan



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
        