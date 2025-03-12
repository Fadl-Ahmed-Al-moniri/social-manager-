from datetime import datetime
import time
from rest_framework import serializers
from posts.models import PostModle

class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostModle
        fields = [
            "id",
            "social_media_account",
            "platform",
            "external_post_id",
            "application",
            "content",
            "media_url",
            "scheduled_at",
            "status",
            "created_at",
            "updated_at",
            "likes_count",
            "comments_count",
            "shares_count",
        ]



    def validate_input(attrs , method):
        if method =="get_posts_page":
            allowed_fields = {"page_id", "platform"}

            for field in allowed_fields:
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError({field: f"This field {field} is required."})
            
            return True
        elif method =="publish":
            allowed_fields = {"page_ids" , "content"}

            for field in allowed_fields:
                print(attrs)
                print(attrs[field])
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError({field: f"This field {field} is required."})

    def validate(self, attrs):
        # view_action = self.context.get('view_action')
        # if view_action == "get_posts_page":
        #     pass
        return super().validate(attrs)