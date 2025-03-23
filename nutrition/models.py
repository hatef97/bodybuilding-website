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
