from django.shortcuts import render
from rest_framework import viewsets,validators,status,decorators
from .serializers import PostInteractionSerializer 
from rest_framework.authentication import TokenAuthentication
from core.permission.permissions import ISManager 
from rest_framework.serializers import ValidationError
from core.services.facebook_services import FacebookService
from core.services.get_user_from_token import get_user_from_token 
from core.services.create_response import create_response 
from core.services.instgram_services import InstgramService
from posts.models import PostModle
from accounts_connection.models import Platform , SocialMediaAccount 
from platform_media.models import FacebookPageModel,FacebookUserModel  , InstagramModel
# Create your views here.




class InteractionsView(viewsets.ViewSet):
    serializer_class = PostInteractionSerializer
    authentication_classes = [TokenAuthentication]

    permission_classes_by_action = {
        'get_post_info': [ISManager],
    }
    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]
        


    @decorators.action(methods=["post"], detail=False, url_path="get_post_info")
    def get_post_info(self, request):
        user_instance = get_user_from_token (request=request)


        try :
            if PostInteractionSerializer.validate_input(attrs=request.data ,method = "get_post_info"):
                post_id_request = request.data.get("post_id")
                platform_request = request.data.get("platform")
                page_id_request = request.data.get("page_id")
                platform_instance=  Platform.objects.get(name=platform_request)
                if platform_instance.name == "Facebook":
                    page_facebook_instance = FacebookPageModel.objects.get(facebook_page_id = page_id_request)
                    response_data = FacebookService.get_interaction_post(access_token=page_facebook_instance.facebook_page_access_token,post_id=post_id_request)
                    return create_response(
                    message=response_data,
                    status_code=status.HTTP_200_OK
                    )

                if platform_instance.name =="Instagram":
                    pass
        except (BaseException, ValidationError) as e:
            return create_response(
                errors="error",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
