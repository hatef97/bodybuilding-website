from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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

    def create(self, validated_data):
        """
        Override the create method to handle nested 'meals' data.
        """
        meals_data = validated_data.pop('meals')  # Extract 'meals' data
        meal_plan = MealPlan.objects.create(**validated_data)  # Create the MealPlan instance

        # Loop through each meal in the meals data and create a meal
        for meal_data in meals_data:
            meal = Meal.objects.create(**meal_data)
            meal_plan.meals.add(meal)  # Add meal to the meal plan

        return meal_plan

    def update(self, instance, validated_data):
        """
        Update the MealPlan instance with validated data.
        """
        # Extract meals data from validated_data
        meals_data = validated_data.pop('meals', [])

        # Update the basic fields first
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update the meals - handle as a nested field
        meal_instances = []

        # If meals are passed as dictionaries, we need to extract their IDs
        if meals_data:
            for meal_data in meals_data:
                # If meal_data is a dict with fields (id, etc.), get the meal instance by ID
                if isinstance(meal_data, dict):
                    meal_instance = Meal.objects.get(id=meal_data['id'])  # Fetch the existing Meal instance
                    # Update the meal with the new data
                    for field, value in meal_data.items():
                        setattr(meal_instance, field, value)
                    meal_instance.save()
                    meal_instances.append(meal_instance)
                else:
                    # If it's just an ID, we fetch the meal instance by ID
                    meal_instance = Meal.objects.get(id=meal_data)
                    meal_instances.append(meal_instance)

        # Set the updated meals to the MealPlan instance
        instance.meals.set(meal_instances)  # Update the meal relationships

        # Save the updated MealPlan instance
        instance.save()

        return instance



class MealInMealPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the MealInMealPlan model, which defines the order of meals in a meal plan.
    """
    meal = serializers.PrimaryKeyRelatedField(queryset=Meal.objects.all())  # Use the meal's ID
    order = serializers.IntegerField(min_value=1)  # Validate that order is a positive value

    class Meta:
        model = MealInMealPlan
        fields = ['id', 'meal_plan', 'meal', 'order']

    def validate(self, data):
        """
        Ensure that the combination of meal and meal_plan is unique.
        """
        meal = data.get('meal')
        meal_plan = data.get('meal_plan')

        # Check if the meal is already in the meal plan
        if MealInMealPlan.objects.filter(meal=meal, meal_plan=meal_plan).exists():
            raise serializers.ValidationError("This meal is already added to the meal plan.")
        
        return data

    def create(self, validated_data):
        # Create the MealInMealPlan instance
        meal_in_meal_plan = MealInMealPlan.objects.create(**validated_data)
        return meal_in_meal_plan



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
    total_calories = serializers.IntegerField(validators=[validate_positive])
    total_protein = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    total_carbs = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
    total_fats = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[validate_positive])
