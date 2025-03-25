from rest_framework import serializers

from .models import Meal, MealPlan, MealInMealPlan, Recipe, CalorieCalculator



# Custom Validator for Macronutrients
def validate_positive(value):
    if value < 0:
        raise serializers.ValidationError("This field must be a positive value.")
    return value



class MealSerializer(serializers.ModelSerializer):
    """
    Serializer for the Meal model, representing a single meal with its nutritional information.
    """
    protein = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    carbs = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    fats = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])

    class Meta:
        model = Meal
        fields = ['id', 'name', 'calories', 'protein', 'carbs', 'fats', 'description']

    def validate(self, data):
        """
        Custom validation to ensure no required fields are missing.
        """
        if not data.get('protein') or not data.get('carbs') or not data.get('fats'):
            raise serializers.ValidationError("Protein, carbs, and fats are required fields.")
        return data



class MealPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the MealPlan model, representing a meal plan with a list of meals and its goal.
    """
    meals = MealSerializer(many=True)

    total_calories = serializers.IntegerField(read_only=True)
    total_protein = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_carbs = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_fats = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = MealPlan
        fields = ['id', 'name', 'goal', 'meals', 'total_calories', 'total_protein', 'total_carbs', 'total_fats']

    def to_representation(self, instance):
        """
        Overriding to include calculated totals in the response.
        """
        representation = super().to_representation(instance)
        representation['total_calories'] = instance.total_calories()
        representation['total_protein'] = instance.total_protein()
        representation['total_carbs'] = instance.total_carbs()
        representation['total_fats'] = instance.total_fats()
        return representation



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
    calories = serializers.IntegerField(validators=[validate_positive])
    protein = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    carbs = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    fats = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'ingredients', 'instructions', 'calories', 'protein', 'carbs', 'fats']



class CalorieCalculatorSerializer(serializers.ModelSerializer):
    """
    Serializer for the CalorieCalculator model, representing user inputs for calorie calculation.
    """
    age = serializers.IntegerField(validators=[validate_positive])
    weight = serializers.FloatField(validators=[validate_positive])
    height = serializers.FloatField(validators=[validate_positive])

    class Meta:
        model = CalorieCalculator
        fields = ['id', 'gender', 'age', 'weight', 'height', 'activity_level', 'goal']

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
