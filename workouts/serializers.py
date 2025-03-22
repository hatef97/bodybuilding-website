from rest_framework import serializers

from .models import Exercise, WorkoutPlan, WorkoutLog
from core.models import CustomUser



class ExerciseSerializer(serializers.ModelSerializer):
    """
    Serializer for Exercise model, which can be used for viewing and creating exercises.
    """
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'category', 'video_url']
        extra_kwargs = {
            'name': {'required': True}, 
            'category': {'required': True, 'allow_null': False},  
        }

    def validate_category(self, value):
        """
        Custom validator for the 'category' field to ensure it is either 'Strength' or 'Cardio'.
        """
        valid_categories = ['Strength', 'Cardio']
        if value not in valid_categories:
            raise serializers.ValidationError("Category must be 'Strength' or 'Cardio'.")
        return value



class WorkoutPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkoutPlan model, which includes a list of exercises.
    """
    exercises = ExerciseSerializer(many=True)

    class Meta:
        model = WorkoutPlan
        fields = ['id', 'name', 'description', 'exercises', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Override the create method to handle nested `exercises` and create a `WorkoutPlan` object.
        """
        exercises_data = validated_data.pop('exercises')
        workout_plan = WorkoutPlan.objects.create(**validated_data)
        for exercise_data in exercises_data:
            Exercise.objects.create(workout_plan=workout_plan, **exercise_data)
        return workout_plan
