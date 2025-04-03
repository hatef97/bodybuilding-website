from rest_framework import serializers

from django.utils import timezone

from progress.models import WeightLog



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
