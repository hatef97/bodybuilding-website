from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError



# ForumPost Model
class ForumPost(models.Model):
    """Forum post where users can create discussions."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255, blank=False)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # To manage post visibility (soft delete feature)
    
    def clean(self):
        """Custom validation to ensure title is not blank."""
        if not self.title.strip():
            raise ValidationError("Title cannot be blank.")

    def save(self, *args, **kwargs):
        """Override save to invoke the clean method and trigger validation."""
        self.full_clean()  # This will call the clean method and raise ValidationError if invalid
        super(ForumPost, self).save(*args, **kwargs)  # Call the actual save method

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']



# Comment Model
class Comment(models.Model):
    """Comment on a forum post."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)  # To manage comment visibility (soft delete feature)
    
    def clean(self):
        """Override the clean method to validate the content field."""
        if not self.content.strip():  # Ensure content is not empty or only whitespace
            raise ValidationError("Comment content cannot be empty.")

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    class Meta:
        ordering = ['created_at']



# Challenge Model
class Challenge(models.Model):
    """Challenge where users can compete with each other."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='challenges')
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def clean(self):
        """Ensure the end date is after the start date."""
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
    
    def __str__(self):
        return self.name



# Leaderboard Model
class Leaderboard(models.Model):
    """Stores leaderboards based on challenge participation or other metrics."""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='leaderboards')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboards')
    score = models.PositiveIntegerField()  # The score could be based on challenge performance, activity, etc.

    def __str__(self):
        return f"{self.user.username} - {self.challenge.name} - {self.score}"

    class Meta:
        ordering = ['-score']
        unique_together = ['challenge', 'user']  # Ensure each user has a unique entry in the leaderboard for each challenge



# User Profile for Forum and Social features
class UserProfile(models.Model):
    """User profile that stores additional information about a user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    social_links = models.JSONField(default=dict, blank=True)  # To store social media links (Facebook, Twitter, etc.)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
