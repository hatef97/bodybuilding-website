from django.db import models



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
