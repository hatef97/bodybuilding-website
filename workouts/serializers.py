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
            exercise = Exercise.objects.create(**exercise_data)
            workout_plan.exercises.add(exercise)
        return workout_plan



class WorkoutLogSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkoutLog model, responsible for logging user workouts.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), write_only=True)
    workout_plan = serializers.PrimaryKeyRelatedField(queryset=WorkoutPlan.objects.all(), write_only=True)
    duration = serializers.IntegerField(min_value=1)  

    class Meta:
        model = WorkoutLog
        fields = ['id', 'user', 'workout_plan', 'date', 'duration', 'notes']
        read_only_fields = ['id', 'date']

    def validate_duration(self, value):
        """
        Ensure that workout duration is reasonable (must be greater than 0).
        """
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than zero.")
        return value

    def create(self, validated_data):
        """
        Create a new workout log entry and associate it with the user and the workout plan.
        """
        user = validated_data['user']
        workout_plan = validated_data['workout_plan']
        log_entry = WorkoutLog.objects.create(**validated_data)
        return log_entry



class UserWorkoutLogSerializer(serializers.ModelSerializer):
    """
    Serializer for aggregating workout logs related to a user.
    """
    workout_plan_name = serializers.CharField(source='workout_plan.name', read_only=True)
    duration = serializers.IntegerField()
    date = serializers.DateField()

    class Meta:
        model = WorkoutLog
        fields = ['workout_plan_name', 'duration', 'date']
        read_only_fields = ['workout_plan_name', 'duration', 'date']

    def to_representation(self, instance):
        """
        Override to_representation to format the data in a user-friendly way.
        """
        representation = super().to_representation(instance)
        representation['date'] = instance.date.strftime('%B %d, %Y')
        return representation
