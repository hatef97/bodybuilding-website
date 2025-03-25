from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from nutrition.models import Meal



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
