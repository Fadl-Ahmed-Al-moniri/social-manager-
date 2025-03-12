from django.db import models
from accounts_connection.models import SocialMediaAccount ,Platform
from django.utils import timezone
from core.utils.get_current_timestamp import get_current_timestamp


class PostModle(models.Model):
    social_media_account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    
    external_post_id = models.CharField(max_length=255, blank=True, null=True)
    application= models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    media_url = models.TextField(blank=True, null=True)
    scheduled_at = models.BigIntegerField(blank=True, null=True)

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('draft', 'Draft'),
    ]

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='published'
    )

    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    likes_count = models.BigIntegerField(default=0)
    comments_count = models.BigIntegerField(default=0)
    shares_count = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.updated_at = get_current_timestamp()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Post {self.external_post_id} - {self.status}"