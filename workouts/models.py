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



class WorkoutPlan(models.Model):
    """
    A model for a workout plan, containing multiple exercises.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    exercises = models.ManyToManyField(Exercise, related_name='workout_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class WorkoutLog(models.Model):
    """
    A model for tracking individual workout sessions.
    """
    user = models.ForeignKey('core.CustomUser', on_delete=models.CASCADE)
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE)
    date = models.DateField()
    duration = models.PositiveIntegerField(help_text="Duration of the workout in minutes.")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.email} - {self.workout_plan.name} ({self.date})'
