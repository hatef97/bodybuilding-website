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



class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Recipe model, representing a recipe with ingredients, instructions, and nutritional info.
    """
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'ingredients', 'instructions', 'calories', 'protein', 'carbs', 'fats']

    def validate_calories(self, value):
        """
        Ensure calories are positive.
        """
        if value < 0:
            raise serializers.ValidationError("Calories must be a positive value.")
        return value

    def validate_protein(self, value):
        """
        Ensure protein is positive.
        """
        if value < 0:
            raise serializers.ValidationError("Protein must be a positive value.")
        return value

    def validate_carbs(self, value):
        """
        Ensure carbs are positive.
        """
        if value < 0:
            raise serializers.ValidationError("Carbs must be a positive value.")
        return value

    def validate_fats(self, value):
        """
        Ensure fats are positive.
        """
        if value < 0:
            raise serializers.ValidationError("Fats must be a positive value.")
        return value



class CalorieCalculatorSerializer(serializers.ModelSerializer):
    """
    Serializer for the CalorieCalculator model, representing user inputs for calorie calculation.
    """
    class Meta:
        model = CalorieCalculator
        fields = ['id', 'gender', 'age', 'weight', 'height', 'activity_level', 'goal']

    def validate_age(self, value):
        """
        Ensure age is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Age must be a positive number.")
        return value

    def validate_weight(self, value):
        """
        Ensure weight is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Weight must be a positive number.")
        return value

    def validate_height(self, value):
        """
        Ensure height is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Height must be a positive number.")
        return value

    def calculate_calories(self, obj):
        """
        Calculate daily caloric requirement based on Harris-Benedict formula.
        """
        return obj.calculate_calories()



class MealPlanSummarySerializer(serializers.Serializer):
    """
    A serializer to show summary data for the meal plan (total calories, protein, carbs, fats).
    """
    total_calories = serializers.IntegerField()
    total_protein = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_carbs = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_fats = serializers.DecimalField(max_digits=5, decimal_places=2)
    