from rest_framework import serializers

from django.core.exceptions import ValidationError

from core.models import CustomUser
from .models import CalorieCalculator, Meal, Recipe, MealPlan



# Serializer for CalorieCalculator model
class CalorieCalculatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalorieCalculator
        fields = ['id', 'gender', 'age', 'weight', 'height', 'activity_level']

    def validate(self, data):
        """Override validate to ensure correct values for age, weight, and height."""

        # Set default values if not provided
        data['gender'] = data.get('gender', 'male')  # Default to 'male' if not provided
        data['activity_level'] = data.get('activity_level', 'sedentary')  # Default to 'sedentary' if not provided
        
        if not data.get('age') or data['age'] <= 0:
            raise serializers.ValidationError("Age must be a positive number.")
        if not data.get('weight') or data['weight'] <= 0:
            raise serializers.ValidationError("Weight must be a positive number.")
        if not data.get('height') or data['height'] <= 0:
            raise serializers.ValidationError("Height must be a positive number.")
        if not data.get('activity_level'):
            raise serializers.ValidationError("Activity level must be provided.")
        if not data.get('gender'):
            raise serializers.ValidationError("Gender must be provided.")
        
        return data

    def create(self, validated_data):
        """Override the create method to calculate calories."""
        instance = super().create(validated_data)
        instance.calculate_calories()
        return instance



# Serializer for Meal model
class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ['id', 'name', 'description', 'calories', 'protein', 'carbs', 'fat']

    def validate(self, data):
        """Override validate to ensure that calories are positive."""

        # Ensure 'calories' is in the data
        if 'calories' not in data:
            raise serializers.ValidationError("Calories field is required.")

        if data['calories'] <= 0:
            raise serializers.ValidationError("Calories must be a positive number.")
        return data



# Serializer for Recipe model
class RecipeSerializer(serializers.ModelSerializer):
    meal = serializers.PrimaryKeyRelatedField(queryset=Meal.objects.all())

    class Meta:
        model = Recipe
        fields = ['id', 'meal', 'instructions', 'ingredients']

    def validate(self, data):
        """Override validate to ensure the instructions and ingredients length are valid."""
        if len(data['instructions']) > 500:
            raise serializers.ValidationError("Instructions cannot exceed 500 characters.")
        if len(data['ingredients']) > 500:
            raise serializers.ValidationError("Ingredients cannot exceed 500 characters.")
        if 'meal' not in data or 'instructions' not in data or 'ingredients' not in data:
            raise serializers.ValidationError("All fields are required.")
        return data

    def create(self, validated_data):
        """Handle the creation of Recipe with nested meal data."""
        meal = validated_data.pop('meal')  # Just the ID is passed from the request
        recipe = Recipe.objects.create(meal=meal, **validated_data)  # Create the Recipe instance with validated data
        return recipe



# Serializer for MealPlan model
class MealPlanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    meals = serializers.PrimaryKeyRelatedField(queryset=Meal.objects.all(), many=True)  # Accept meal IDs

    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'name', 'description', 'meals']

    def validate_meals(self, value):
        """Ensure that meals are not empty."""
        if not value:
            raise serializers.ValidationError("At least one meal must be provided.")
        return value

    def create(self, validated_data):
        """Handle creation of MealPlan with related meals."""
        meals_data = validated_data.pop('meals')
        meal_plan = MealPlan.objects.create(**validated_data)

        # Add meals to the meal plan
        meal_plan.meals.set(meals_data)  # Using set to handle the many-to-many relationship
        meal_plan.save()

        return meal_plan

    def update(self, instance, validated_data):
        """Handle update of an existing meal plan and its related data."""
        meals_data = validated_data.pop('meals', None)

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        if meals_data:
            instance.meals.set(meals_data)  # Using set to update the many-to-many relationship

        return instance
