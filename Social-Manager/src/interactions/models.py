from django.db import models
from accounts_connection.models import Platform
from posts.models import PostModle
# Create your models here.

class PostInteractionModel(models.Model):

    post_id =  models.ForeignKey(
        PostModle,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    
    STATUS_CHOICES = [
        ('like', 'like'),
        ('comment', 'comment'),
        ('share', 'share'),
    ]

    interaction_type = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='like'
    )

    interaction_date = models.BigIntegerField(blank=True, null=True)
    
    external_user_id  = models.BigIntegerField(blank=True, null=True)
    external_post_id   = models.BigIntegerField(blank=True, null=True)
    external_interaction_id   = models.BigIntegerField(blank=True, null=True)