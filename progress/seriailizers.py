from rest_framework import serializers

from django.utils import timezone

from .models import WeightLog, BodyMeasurement, ProgressLog



class WeightLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    date_logged = serializers.DateField(read_only=True)

    class Meta:
        model = WeightLog
        fields = ['id', 'user', 'weight_kg', 'date_logged']
        read_only_fields = ['id', 'date_logged']  # Prevent user from overriding date

    def validate(self, data):
        """
        Prevent a user from creating multiple logs for the same day.
        """
        user = self.context['request'].user
        today = data.get('date_logged') or timezone.now().date()

        if WeightLog.objects.filter(user=user, date_logged=today).exists():
            raise serializers.ValidationError("You have already logged your weight today.")

        return data



class BodyMeasurementSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    date_logged = serializers.DateField(read_only=True)

    class Meta:
        model = BodyMeasurement
        fields = [
            'id',
            'user',
            'chest_cm',
            'waist_cm',
            'hips_cm',
            'biceps_cm',
            'thighs_cm',
            'calves_cm',
            'neck_cm',
            'date_logged'
        ]
        read_only_fields = ['id', 'date_logged']

    def validate(self, data):
        """
        Prevent duplicate measurements for the same user on the same date.
        """
        user = self.context['request'].user
        today = timezone.now().date()

        if BodyMeasurement.objects.filter(user=user, date_logged=today).exists():
            raise serializers.ValidationError("You have already submitted body measurements for today.")

        return data



class ProgressLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = serializers.ImageField(required=False, allow_null=True)
    date_logged = serializers.DateField(read_only=True)

    class Meta:
        model = ProgressLog
        fields = ['id', 'user', 'title', 'note', 'image', 'date_logged']
        read_only_fields = ['id', 'date_logged']

    def validate(self, data):
        """
        prevent duplicate logs for the same day.
        """
        user = self.context['request'].user
        today = timezone.now().date()

        if ProgressLog.objects.filter(user=user, date_logged=today).exists():
            raise serializers.ValidationError("You already have a progress log for today.")

        return data
