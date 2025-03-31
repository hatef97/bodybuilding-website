from django.db import models
from django.core.exceptions import ValidationError



def validate_positive(value):
    """Validator to ensure the value is positive (no zero or negative values)."""
    if value <= 0:
        raise ValidationError(f"{value} is not a valid value. The value must be positive.")



class CalorieCalculator(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    ACTIVITY_LEVEL_CHOICES = (
        ('sedentary', 'Sedentary'),
        ('light_activity', 'Light Activity'),
        ('moderate_activity', 'Moderate Activity'),
        ('heavy_activity', 'Heavy Activity'),
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='male',
    )
    age = models.PositiveIntegerField()
    weight = models.PositiveIntegerField(help_text="Weight in kg")
    height = models.PositiveIntegerField(help_text="Height in cm")
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES,
        default='sedentary',
    )

    def clean(self):
        """Custom validation for age, weight, height."""
        if self.gender not in [choice[0] for choice in self.GENDER_CHOICES]:
            raise ValidationError(f"Invalid gender: {self.gender}. Choose either 'male' or 'female'.")
        
        if self.activity_level not in [choice[0] for choice in self.ACTIVITY_LEVEL_CHOICES]:
            raise ValidationError(f"Invalid activity level: {self.activity_level}. Choose from 'sedentary', 'light_activity', 'moderate_activity', 'heavy_activity'.")
        
        if self.age <= 0:
            raise ValidationError("Age must be a positive number.")
        if self.weight <= 0:
            raise ValidationError("Weight must be a positive number.")
        if self.height <= 0:
            raise ValidationError("Height must be a positive number.")

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



class Meal(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default="No description provided.")
    calories = models.PositiveIntegerField(default=0 ,help_text="Calories per serving")
    protein = models.PositiveIntegerField(default=0 ,help_text="Protein per serving in grams")
    carbs = models.PositiveIntegerField(default=0 ,help_text="Carbs per serving in grams")
    fat = models.PositiveIntegerField(default=0 ,help_text="Fat per serving in grams")

    def clean(self):
        """Override the clean method to validate"""
        if self.calories <= 0:
            raise ValidationError("Calories must be a positive number.")

    def __str__(self):
        return self.name



class Recipe(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='recipes')
    instructions = models.TextField()
    ingredients = models.TextField()

    def clean(self):
        """Override the clean method to validate the length of instructions."""
        max_length = 500
        if len(self.instructions) > max_length:
            raise ValidationError(f"Instructions cannot exceed {max_length} characters.")
        if len(self.ingredients) > max_length:
            raise ValidationError(f"Ingredients cannot exceed {max_length} characters.")

    def __str__(self):
        return f"Recipe for {self.meal.name}"



class MealPlan(models.Model):
    user = models.ForeignKey('core.CustomUser', on_delete=models.CASCADE, related_name='meal_plans_user')
    name = models.CharField(max_length=255)
    description = models.TextField(default="No description provided.")
    meals = models.ManyToManyField(Meal, related_name='meal_plans_meal')

    def __str__(self):
        return self.name



# class MealInMealPlan(models.Model):
#     meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE)
#     meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)

#     class Meta:
#         unique_together = ('meal_plan', 'meal')

#     def __str__(self):
#         return f"{self.meal.name} in {self.meal_plan.name}"
