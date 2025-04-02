from django.db import models
from django.conf import settings
from django.utils import timezone



class WeightLog(models.Model):
    """
    Tracks a user's weight over time.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weight_logs')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kilograms")
    date_logged = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date_logged']
        verbose_name = 'Weight Log'
        verbose_name_plural = 'Weight Logs'
        unique_together = ('user', 'date_logged')

    def __str__(self):
        return f"{self.user} - {self.weight_kg}kg on {self.date_logged.date()}"



class BodyMeasurement(models.Model):
    """
    Stores detailed body measurements for a user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='body_measurements')
    chest_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    biceps_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    thighs_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calves_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    neck_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    date_logged = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date_logged']
        verbose_name = 'Body Measurement'
        verbose_name_plural = 'Body Measurements'
        unique_together = ('user', 'date_logged')

    def __str__(self):
        return f"{self.user} measurements on {self.date_logged}"



class ProgressLog(models.Model):
    """
    Allows users to write notes about their progress, including milestones or reflections.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_logs')
    title = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True, help_text="User's personal notes or fitness reflections.")
    image = models.ImageField(upload_to='progress_photos/', null=True, blank=True, help_text="Optional progress photo.")
    date_logged = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date_logged']
        verbose_name = 'Progress Log'
        verbose_name_plural = 'Progress Logs'

    def __str__(self):
        return f"{self.user} progress log on {self.date_logged}"
        