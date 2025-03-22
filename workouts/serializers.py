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
        