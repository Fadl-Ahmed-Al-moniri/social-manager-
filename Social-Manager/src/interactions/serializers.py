from rest_framework import serializers 
from core.services.facebook_services import FacebookService
from accounts_connection.models import SocialMediaAccount
from .models import PostInteractionModel



class PostInteractionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PostInteractionModel
        fields = [
            "id",
            "post_id",
            "interaction_type",
            "interaction_date",
            "external_user_id",
            "external_post_id",
            "external_interaction_id",
        ]


    def validate_input(attrs , method):
        if method =="get_post_info":
            allowed_fields = {"post_id", "platform" ,"page_id"}

            for field in allowed_fields:
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError({field: f"This field {field} is required."})
            
            return True
        