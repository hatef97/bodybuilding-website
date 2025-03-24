from django.core.exceptions import ValidationError
from django.db import models

from decimal import Decimal



class Meal(models.Model):
    """
    Meal model to store meal information.
    """
    name = models.CharField(max_length=255)
    calories = models.PositiveIntegerField(help_text="Total calories for the meal")
    protein = models.DecimalField(max_digits=5, decimal_places=2, help_text="Amount of protein (grams)")
    carbs = models.DecimalField(max_digits=5, decimal_places=2, help_text="Amount of carbs (grams)")
    fats = models.DecimalField(max_digits=5, decimal_places=2, help_text="Amount of fats (grams)")
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Meal"
        verbose_name_plural = "Meals"

    def __str__(self):
        return self.name

    def clean(self):
        """
        Custom validation to ensure macronutrients are not negative.
        """
        if self.protein < 0:
            raise ValidationError("Protein must be a positive value.")
        if self.carbs < 0:
            raise ValidationError("Carbs must be a positive value.")
        if self.fats < 0:
            raise ValidationError("Fats must be a positive value.")



class MealPlan(models.Model):
    """
    Meal Plan for different fitness goals like bulking, cutting, and maintenance.
    """
    GOAL_CHOICES = [
        ('bulking', 'Bulking'),
        ('cutting', 'Cutting'),
        ('maintenance', 'Maintenance'),
    ]
    name = models.CharField(max_length=255)
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES)
    meals = models.ManyToManyField(Meal, related_name='meal_plans', through='MealInMealPlan')

    class Meta:
        verbose_name = "Meal Plan"
        verbose_name_plural = "Meal Plans"

    def __str__(self):
        return f'{self.name} ({self.get_goal_display()})'

    def total_calories(self):
        """
        Calculate the total calories for the meal plan by summing the calories of all meals.
        """
        return sum(meal.calories for meal in self.meals.all())

    def total_protein(self):
        """
        Calculate the total protein for the meal plan.
        """
        return sum(meal.protein for meal in self.meals.all())

    def total_carbs(self):
        """
        Calculate the total carbs for the meal plan.
        """
        return sum(meal.carbs for meal in self.meals.all())

    def total_fats(self):
        """
        Calculate the total fats for the meal plan.
        """
        return sum(meal.fats for meal in self.meals.all())



class MealInMealPlan(models.Model):
    """
    An intermediary model for many-to-many relationship between MealPlan and Meal.
    Includes ordering for meals in a plan.
    """
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1, help_text="The order of this meal in the plan")

    class Meta:
        ordering = ['order']
        unique_together = ['meal_plan', 'meal']

    def __str__(self):
        return f"{self.meal.name} in {self.meal_plan.name}"



class Recipe(models.Model):
    """
    Recipe model to store recipe information.
    """
    name = models.CharField(max_length=255)
    ingredients = models.TextField(help_text="List of ingredients")
    instructions = models.TextField(help_text="Preparation steps")
    calories = models.PositiveIntegerField()
    protein = models.DecimalField(max_digits=5, decimal_places=2)
    carbs = models.DecimalField(max_digits=5, decimal_places=2)
    fats = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"

    def __str__(self):
        return self.name

    def clean(self):
        """
        Custom clean method to ensure all values are positive.
        """
        if self.calories < 0:
            raise ValidationError("Calories must be a positive value.")
        if self.protein < 0:
            raise ValidationError("Protein must be a positive value.")
        if self.carbs < 0:
            raise ValidationError("Carbs must be a positive value.")
        if self.fats < 0:
            raise ValidationError("Fats must be a positive value.")
            


class CalorieCalculator(models.Model):
    """
    Model for calculating daily calorie requirements.
    """
    gender_choices = [
        ('male', 'Male'),
        ('female', 'Female')
    ]

    gender = models.CharField(max_length=10, choices=gender_choices)
    age = models.PositiveIntegerField()
    weight = models.FloatField(help_text="Weight in kg")
    height = models.FloatField(help_text="Height in cm")
    activity_level = models.CharField(max_length=50, choices=[
        ('sedentary', 'Sedentary'),
        ('light_activity', 'Light Activity'),
        ('moderate_activity', 'Moderate Activity'),
        ('heavy_activity', 'Heavy Activity')
    ])
    goal = models.CharField(max_length=50, choices=[
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight')
    ])

    class Meta:
        verbose_name = "Calorie Calculator"
        verbose_name_plural = "Calorie Calculators"

    def calculate_calories(self):
        """
        Simple Harris-Benedict formula for daily caloric requirement calculation.
        """
        if self.gender == 'male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

        if self.activity_level == 'sedentary':
            return bmr * 1.2
        elif self.activity_level == 'light_activity':
            return bmr * 1.375
        elif self.activity_level == 'moderate_activity':
            return bmr * 1.55
        else:
            return bmr * 1.725

    def __str__(self):
        return f'Calorie Calculation for {self.gender} ({self.age} years)'
