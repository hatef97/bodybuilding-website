from django.db import models


class Exercise(models.Model):
    """
    A model for an exercise that can be part of a workout plan.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, choices=[('Strength', 'Strength'), ('Cardio', 'Cardio')])
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
        