from django.contrib import admin

from posts.models import PostModle
# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_display = [ 'social_media_account', 'platform', 'external_post_id','content','likes_count' ]
    list_filter = ['platform','application']

admin.site.register(PostModle,PostAdmin)

