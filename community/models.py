# community/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError



# ForumPost Model
class ForumPost(models.Model):
    """Forum post where users can create discussions."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # To manage post visibility (soft delete feature)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        