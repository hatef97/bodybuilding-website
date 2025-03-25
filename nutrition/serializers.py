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



class MealPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the MealPlan model, representing a meal plan with a list of meals and its goal.
    """
    meals = MealSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlan
        fields = ['id', 'name', 'goal', 'meals']

    def get_total_calories(self, obj):
        """
        Calculate the total calories of the meal plan.
        """
        return obj.total_calories()

    def get_total_protein(self, obj):
        """
        Calculate the total protein of the meal plan.
        """
        return obj.total_protein()

    def get_total_carbs(self, obj):
        """
        Calculate the total carbs of the meal plan.
        """
        return obj.total_carbs()

    def get_total_fats(self, obj):
        """
        Calculate the total fats of the meal plan.
        """
        return obj.total_fats()



class MealInMealPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the MealInMealPlan model, which defines the order of meals in a meal plan.
    """
    meal = MealSerializer()

    class Meta:
        model = MealInMealPlan
        fields = ['id', 'meal_plan', 'meal', 'order']

    def validate_order(self, value):
        """
        Ensure that the order is a positive integer.
        """
        if value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value
        