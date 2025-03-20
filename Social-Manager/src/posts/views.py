import json
from django.http import HttpResponse
from django.shortcuts import   get_object_or_404
from itertools import groupby
from operator import attrgetter
import asyncio
from rest_framework import response, viewsets ,decorators , status
from rest_framework.authentication import TokenAuthentication
from posts.models import PostModle
from posts.serializers import PostSerializer
from accounts_connection.models import SocialMediaAccount, Platform
from platform_media.models import FacebookPageModel , InstagramModel
from core.services.create_response import create_response 
from core.services.get_user_from_token import get_user_from_token
from core.services.facebook_services import FacebookService 
from core.services.instgram_services  import InstgramService 
from core.utils.get_current_timestamp import  get_current_timestamp 
from core.utils.prepare_facebook_posts_data import  prepare_facebook_posts_data 
from rest_framework.serializers import ValidationError
from django.db.models import Q
from core.permission.permissions import ISManager , IsPublishingEmp
from asgiref.sync import sync_to_async
from core.utils.get_current_timestamp import get_current_timestamp
from django.utils import timezone




class PostView(viewsets.ViewSet ):
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes_by_action = {
        'get_posts_page': [ IsPublishingEmp],
        'publish': [ IsPublishingEmp],
    }
    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]


    @decorators.action(methods=["post"], detail=False, url_path="get_posts_page")
    def get_posts_page(self, request):
        user_instance = get_user_from_token(request=request)
        print(request.data)
        try:
            if not user_instance.manager is None:
                    user_instance = user_instance.manager
            if PostSerializer.validate_input(attrs=request.data ,method = "get_posts_page"):
                
                platform_instance = Platform.objects.get(name=request.data.get("platform"))
                
                if platform_instance.name == "Facebook":
                    social_instance =  SocialMediaAccount.objects.get(user = user_instance , external_account_id = request.data.get("page_id"))
                    page_instance = FacebookPageModel.objects.get(social_media_account = social_instance, facebook_page_id=request.data.get("page_id"))
                    data = request.data.copy()
                    
                    data["platform"] = platform_instance.pk
                    data["social_media_account"] = page_instance.social_media_account.pk
                    serializer = PostSerializer(data=data, context={'request': request, "get_posts_page": "post"})
                    saved_posts = []

                    if serializer.is_valid():
                        access_token = page_instance.facebook_page_access_token
                        facebook_data = FacebookService.get_facebook_posts(access_token, page_instance.facebook_page_id)

                        for publish_data in facebook_data.get("data", []):
                            prepared_data = prepare_facebook_posts_data(publish_data, page_instance, platform_instance)
                            post_serializer = PostSerializer(data=prepared_data)
                            if not PostModle.objects.filter(external_post_id= post_serializer.initial_data.get("external_post_id")).exists ():
                                
                                if post_serializer.is_valid():
                                    post_serializer.save()
                                    saved_posts.append(post_serializer.data)
                                else:
                                    return create_response(
                                        errors="error",
                                        message=post_serializer.errors,
                                        status_code=status.HTTP_400_BAD_REQUEST
                                    )
                            print("continue")
                            continue

                        return create_response(
                            data=saved_posts,
                            message="Posts saved successfully",
                            status_code=status.HTTP_200_OK
                        )
                    
                    return create_response(
                        errors="error",
                        message=serializer.errors,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                if platform_instance.name =="Instagram":
                    social_instance =  SocialMediaAccount.objects.get(user = user_instance , external_account_id = request.data.get("page_id"))
                    page_instance =InstagramModel.objects.get(social_media_account = social_instance,instagram_id=request.data.get("page_id"))
                    data = request.data.copy()
                    
                    data["platform"] = platform_instance.pk
                    data["social_media_account"] = page_instance.social_media_account.pk
                    access_token = page_instance.instagram_access_token
                    access_token = page_instance.instagram_access_token
                    serializer = PostSerializer(data=data, context={'request': request, "get_posts_page": "post"})
                    saved_posts = []
                    if serializer.is_valid():
                        access_token = page_instance.instagram_access_token
                        media_info = InstgramService.get_media_info(access_token,page_instance.instagram_id,platform_instance,page_instance)
                        post_serializer  = PostSerializer(data = media_info , many = True)
                        # if not PostModle.objects.filter(external_post_id= post_serializer.initial_data.get("external_post_id")).exists ():
                        if post_serializer.is_valid():
                                    post_serializer.save()
                                    return create_response(
                                        message=post_serializer.data,
                                        status_code=status.HTTP_201_CREATED
                                    )
                        else:
                                    return create_response(
                                        errors="error",
                                        message=post_serializer.errors,
                                        status_code=status.HTTP_400_BAD_REQUEST
                                    )

                    return create_response(
                            errors="error",
                            message=str(e),
                            status_code=status.HTTP_400_BAD_REQUEST
                        )

        except (BaseException, ValidationError) as e:
            return create_response(
                errors="error",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


    @decorators.action(methods=["post"], detail=False, url_path="publish")
    def publish(self, request):
        user_instance = get_user_from_token(request=request)
        try:
            if not user_instance.manager is None:
                user_instance = user_instance.manager

            page_ids = request.data.get("page_ids", [])
            publish_type = request.data.get("publish_type")
            print(f"Request Data: {request.data}")
            print(f"Page IDs (from request): {page_ids}")
            print(f"Type of Page IDs: {type(page_ids)}")

            if isinstance(page_ids, str):
                try:
                    page_ids = json.loads(page_ids)
                except json.JSONDecodeError:
                    return create_response(
                        errors="error",
                        message="Invalid format for page_ids. Expected a JSON array.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            print(page_ids)

            if not isinstance(page_ids, list):
                return create_response(
                    errors="error",
                    message="page_ids must be a list.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            page_ids = [str(page_id) for page_id in page_ids]
            print(f"Page IDs (as strings): {page_ids}")

            print(page_ids)

            social_accounts = SocialMediaAccount.objects.filter(
                Q(user=user_instance) & Q(external_account_id__in=page_ids)
            )

            print(f"Social Accounts: {social_accounts}")

            if not social_accounts:
                return create_response(
                    errors="error",
                    message="No social accounts found for the provided page_ids.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            grouped_pages = {
                platform: list(pages)
                for platform, pages in groupby(
                    sorted(social_accounts, key=attrgetter("platform.name")),
                    key=attrgetter("platform.name")
                )
            }

            print(f"Grouped Pages: {grouped_pages}")
            print(f"post_data : {request.data.get("publish_data", {})}")

            if publish_type =="post":
                pass
                # تنفيذ النشر بشكل غير متزامن
                # asyncio.run(self.publish_post_async(publish_type,grouped_pages, request.data.get("publish_data", {})))
                # إرجاع رسالة نجاح
            
            if publish_type =="reels":
                pass

                # asyncio.run(self.publish_reel_async(publish_type,grouped_pages, request.data.get("publish_data", {})))

            return create_response(
                message="Posts published successfully.",
                status_code=status.HTTP_200_OK
            )

        except (BaseException, ValidationError)  as e:
            return create_response(
                errors="error",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


    @decorators.action(methods=["post"], detail=False, url_path="update_post")
    def update_post(self, request):
        try:
            user_instance = get_user_from_token(request=request)
            if PostSerializer.validate_input(request.data, "update_post"):
                post_id = request.data.get("post_id")
                new_content = request.data.get("new_content")
                post_instance = PostModle.objects.get(external_post_id=post_id)

                if post_instance.platform.name == "Facebook":
                    # الحصول على صفحة الفيسبوك المرتبطة بالحساب الاجتماعي
                    facebook_page_instance = FacebookPageModel.objects.get(
                        social_media_account=post_instance.social_media_account
                    )

                    # تحديث المنشور على الفيسبوك
                    update = FacebookService.update_post(
                        access_token=facebook_page_instance.facebook_page_access_token,
                        page_post_id=post_instance.external_post_id,
                        post_message=new_content,
                    )

                    if update:
                        post_instance.content = new_content
                        post_instance.updated_at = int(timezone.now().timestamp())
                        post_instance.save()

                elif post_instance.platform.name == "Instagram":
                    pass
                    # # الحصول على صفحة الإنستجرام المرتبطة بالحساب الاجتماعي
                    # instagram_page_instance = await sync_to_async(InstagramPageModel.objects.get)(
                    #     social_media_account=post_instance.social_media_account
                    # )

                    # # تحديث المنشور على الإنستجرام
                    # update = await sync_to_async(InstagramService.update_post)(
                    #     access_token=instagram_page_instance.instagram_page_access_token,
                    #     post_id=post_instance.external_post_id,
                    #     caption=new_content,
                    # )

                    # if update:
                    #     post_instance.content = new_content
                    #     post_instance.updated_at = int(timezone.now().timestamp())
                    #     await sync_to_async(post_instance.save)()
                return create_response(
                        message="Post updated successfully.",
                        status_code=status.HTTP_200_OK
                    )

        except (BaseException, ValidationError) as e:
            return create_response(
                errors="error",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @decorators.action(methods=["post"], detail=False, url_path="delete_post")
    def delete_post(self, request):
        try:
            user_instance = get_user_from_token(request=request)
            if PostSerializer.validate_input(request.data, "delete_post"):
                post_id = request.data.get("post_id")
                post_instance = PostModle.objects.get(external_post_id=post_id)

                if post_instance.platform.name == "Facebook":
                    # الحصول على صفحة الفيسبوك المرتبطة بالحساب الاجتماعي
                    facebook_page_instance = FacebookPageModel.objects.get(
                        social_media_account=post_instance.social_media_account
                    )

                    # تحديث المنشور على الفيسبوك
                    delete = FacebookService.delete_post(
                        access_token=facebook_page_instance.facebook_page_access_token,
                        post_id=post_id
                    )

                    if delete:
                        post_instance.delete()

                elif post_instance.platform.name == "Instagram":
                    pass
                    # # الحصول على صفحة الإنستجرام المرتبطة بالحساب الاجتماعي
                    # instagram_page_instance = await sync_to_async(InstagramPageModel.objects.get)(
                    #     social_media_account=post_instance.social_media_account
                    # )

                    # # تحديث المنشور على الإنستجرام
                    # update = await sync_to_async(InstagramService.update_post)(
                    #     access_token=instagram_page_instance.instagram_page_access_token,
                    #     post_id=post_instance.external_post_id,
                    #     caption=new_content,
                    # )

                    # if update:
                    #     post_instance.content = new_content
                    #     post_instance.updated_at = int(timezone.now().timestamp())
                    #     await sync_to_async(post_instance.save)()
                return create_response(
                        message="Post updated successfully.",
                        status_code=status.HTTP_200_OK
                    )

        except (BaseException, ValidationError) as e:
            return create_response(
                errors="error",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


    def update_post_async(self, post_instance, new_content):
        """
        تحديث المنشور بشكل غير متزامن بناءً على المنصة.
        """
        try:
            # الحصول على اسم المنصة بشكل متزامن
            platform_name = lambda: post_instance.platform.name

            if platform_name == "Facebook":
                # الحصول على صفحة الفيسبوك المرتبطة بالحساب الاجتماعي
                facebook_page_instance = FacebookPageModel.objects.get(
                    social_media_account=post_instance.social_media_account
                )

                # تحديث المنشور على الفيسبوك
                update = FacebookService.update_post(
                    access_token=facebook_page_instance.facebook_page_access_token,
                    page_post_id=post_instance.external_post_id,
                    post_message=new_content,
                )

                if update:
                    post_instance.content = new_content
                    post_instance.updated_at = int(timezone.now().timestamp())
                    post_instance.save()

            elif platform_name == "Instagram":
                pass
                # # الحصول على صفحة الإنستجرام المرتبطة بالحساب الاجتماعي
                # instagram_page_instance = await sync_to_async(InstagramPageModel.objects.get)(
                #     social_media_account=post_instance.social_media_account
                # )

                # # تحديث المنشور على الإنستجرام
                # update = await sync_to_async(InstagramService.update_post)(
                #     access_token=instagram_page_instance.instagram_page_access_token,
                #     post_id=post_instance.external_post_id,
                #     caption=new_content,
                # )

                # if update:
                #     post_instance.content = new_content
                #     post_instance.updated_at = int(timezone.now().timestamp())
                #     await sync_to_async(post_instance.save)()
        except Exception as e:
            raise ValueError(f"Failed to update post: {e}")


    async def publish_post_async(self, publish_type,grouped_pages, publish_data):
        """
        تنفيذ النشر بشكل غير متزامن.
        """
        for platform, page_ids in grouped_pages.items():
            for page_id in page_ids:
                try:
                    print(page_id)
                    if platform == "Facebook":
                        platform_instance = await sync_to_async(Platform.objects.get)(name = platform)
                        page = await sync_to_async(FacebookPageModel.objects.get)(social_media_account=page_id)
                        post = await sync_to_async(FacebookService.post)(
                            access_token=page.facebook_page_access_token,
                            page_id=page.facebook_page_id,
                            post_message=publish_data.get("content",""),
                            image_path=publish_data.get("media_url",""),
                            link=publish_data.get("links",""),
                            at_time=publish_data.get("scheduled_at",""),
                        )
                        if post :
                            await sync_to_async(PostModle.objects.create)(social_media_account = page_id  ,
                                                    platform = platform_instance ,
                                                    external_post_id =post["post_id"] or post["id"] ,
                                                    content=publish_data.get("content",""),
                                                    media_url = post["id"] if "post_id" in post else None,
                                                    scheduled_at =int(publish_data.get("scheduled_at","")) if publish_data.get("scheduled_at") else None,
                                                    status =publish_data.get("status", ""),
                                                    links = publish_data.get("links",""),
                                                    tags = publish_data.get("tags",""),
                                                    hashtags = publish_data.get("hashtags",""),
                                                    media_type = publish_data.get("media_type",""),
                                                    publish_type = publish_type,
                                                    created_at =int(publish_data.get("created_at","")) if publish_data.get("created_at") else get_current_timestamp(),
                                                    )
                    
                    elif platform == "Instagram":
                        platform_instance = await sync_to_async(Platform.objects.get)(name = platform)
                        page = await sync_to_async(InstagramModel.objects.get)(social_media_account=page_id)
                        post = await sync_to_async(InstgramService.publish_post_to_instagram)(
                            access_token=page.instagram_access_token,
                            page_user_id=page.instagram_id,
                            caption=publish_data.get("content",""),
                            media_urls =  (publish_data.get("media_url","")),
                            user_tags =  publish_data.get("tags",""),
                            media_type="IMAGE"
                        )
                        if post :
                            await sync_to_async(PostModle.objects.create)(social_media_account = page_id  ,
                                                    platform = platform_instance ,
                                                    external_post_id =post["id"] ,
                                                    content=publish_data.get("content",""),
                                                    media_url = post["id"] if "post_id" in post else None,
                                                    scheduled_at =int(publish_data.get("scheduled_at","")) if publish_data.get("scheduled_at") else None,
                                                    status =publish_data.get("status" , ""),
                                                    links = publish_data.get("links",""),
                                                    tags = publish_data.get("tags",""),
                                                    hashtags = publish_data.get("hashtags",""),
                                                    media_type = publish_data.get("media_type",""),
                                                    publish_type = publish_type,
                                                    created_at =int(publish_data.get("created_at","")) if publish_data.get("created_at") else get_current_timestamp(),
                                                    )
                
                except Exception as e:
                    raise ValueError(f"Failed to publish to {platform} page {page_id}: {e}")


    async def publish_reel_async(self, publish_type,grouped_pages, publish_data):

        for platform, page_ids in grouped_pages.items():
            for page_id in page_ids:
                try:
                    print(page_id)
                    if platform == "Facebook":
                        platform_instance = await sync_to_async(Platform.objects.get)(name = platform)
                        page = await sync_to_async(FacebookPageModel.objects.get)(social_media_account=page_id)
                        
                        description = f"{publish_data.get("content","")} \n{publish_data.get("links","")}"
                        post = await sync_to_async(FacebookService.post_reel_to_page)(
                            access_token=page.facebook_page_access_token,
                            page_id=page.facebook_page_id,
                            description=description,
                            video_path=publish_data.get("media_url",""),
                            scheduled_publish_time=publish_data.get("scheduled_at",""),
                        )
                        if post["success"] ==  True :
                            await sync_to_async(PostModle.objects.create)(social_media_account = page_id  ,
                                                    platform = platform_instance ,
                                                    external_post_id =post["video_id"]# or post["id"] ,
                                                    ,content=publish_data.get("content",""),
                                                    media_url = post["video_url"],
                                                    scheduled_at =int(publish_data.get("scheduled_at","")) if publish_data.get("scheduled_at") else None,
                                                    status =publish_data.get("status", ""),
                                                    links = publish_data.get("links",""),
                                                    tags = publish_data.get("tags",""),
                                                    hashtags = publish_data.get("hashtags",""),
                                                    media_type = publish_data.get("media_type",""),
                                                    publish_type = publish_type,
                                                    created_at =int(publish_data.get("created_at","")) if publish_data.get("created_at") else get_current_timestamp(),
                                                    )

                    elif platform == "Instagram":
                        platform_instance = await sync_to_async(Platform.objects.get)(name = platform)
                        page = await sync_to_async(InstagramModel.objects.get)(social_media_account=page_id)
                        description = f"{publish_data.get("content","")} \n{publish_data.get("links","")}"
                        post = await sync_to_async(InstgramService.publish_reel_to_instagram)(
                            access_token=page.instagram_access_token,
                            page_user_id=page.instagram_id,
                            caption=description,
                            video_url =  (publish_data.get("media_url","")),
                            user_tags =  publish_data.get("tags",""),
                            
                        )
                        if post :
                            await sync_to_async(PostModle.objects.create)(social_media_account = page_id  ,
                                                    platform = platform_instance ,
                                                    external_post_id =post["id"] ,
                                                    content=publish_data.get("content",""),
                                                    media_url = post["video_url"],
                                                    scheduled_at =int(publish_data.get("scheduled_at","")) if publish_data.get("scheduled_at") else None,
                                                    status =publish_data.get("status" , ""),
                                                    links = publish_data.get("links",""),
                                                    tags = publish_data.get("tags",""),
                                                    hashtags = publish_data.get("hashtags",""),
                                                    media_type = publish_data.get("media_type",""),
                                                    publish_type = publish_type,
                                                    created_at =int(publish_data.get("created_at","")) if publish_data.get("created_at") else get_current_timestamp(),
                                                    )
                
                except Exception as e:
                    raise ValueError(f"Failed to publish to {platform} page {page_id}: {e}")
