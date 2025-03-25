from rest_framework import serializers

from .models import Meal, MealPlan, MealInMealPlan, Recipe, CalorieCalculator



class MealSerializer(serializers.ModelSerializer):
    """
    Serializer for the Meal model, representing a single meal with its nutritional information.
    """
    class Meta:
        model = Meal
        fields = ['id', 'name', 'calories', 'protein', 'carbs', 'fats', 'description']

    def validate_protein(self, value):
        """
        Ensure protein value is positive.
        """
        if value < 0:
            raise serializers.ValidationError("Protein must be a positive value.")
        return value

    def validate_carbs(self, value):
        """
        Ensure carbs value is positive.
        """
        if value < 0:
            raise serializers.ValidationError("Carbs must be a positive value.")
        return value

    def validate_fats(self, value):
        """
        Ensure fats value is positive.
        """
        if value < 0:
            raise serializers.ValidationError("Fats must be a positive value.")
        return value
