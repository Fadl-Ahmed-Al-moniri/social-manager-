from django.contrib import admin
from django.utils import timezone
from .models import PostModle

class PostAdmin(admin.ModelAdmin):
    list_display = [
        'social_media_account', 
        'platform', 
        'external_post_id', 
        'content', 
        'likes_count', 
        'formatted_created_at' 
    ]
    list_filter = ['platform', 'application' ]

    def formatted_created_at(self, obj):
        """
        تحويل created_at من Unix Timestamp إلى تنسيق تاريخ عادي.
        """
        if obj.created_at:
            return timezone.datetime.fromtimestamp(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
        return "N/A"

    # إضافة وصف للعمود في واجهة الإدارة
    formatted_created_at.short_description = 'Created At'

admin.site.register(PostModle, PostAdmin)