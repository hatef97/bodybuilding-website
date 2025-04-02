from django.db import models
from django.conf import settings



class WeightLog(models.Model):
    """
    Tracks a user's weight over time.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weight_logs')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kilograms")
    date_logged = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date_logged']
        verbose_name = 'Weight Log'
        verbose_name_plural = 'Weight Logs'
        unique_together = ('user', 'date_logged')

    def __str__(self):
        return f"{self.user} - {self.weight_kg}kg on {self.date_logged}"
