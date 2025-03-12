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
from core.services.connect_facebook_pages import prepare_facebook_post_data 
from rest_framework.serializers import ValidationError
from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async



class PostView(viewsets.ViewSet ):
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    # permission_classes_by_action = {
    #     'get_info': [ISManager],    }

    # def get_permissions(self):
    #     try:
    #         return [permission() for permission in self.permission_classes_by_action[self.action]]
    #     except KeyError:
    #         return [permission() for permission in self.permission_classes]

    @decorators.action(methods=["post"], detail=False, url_path="get_posts_page")
    def get_posts_page(self, request):
        user_instance = get_user_from_token(request=request)
        print(request.data)
        try:
            if PostSerializer.validate_input(attrs=request.data ,method = "get_posts_page"):
                platform_instance = Platform.objects.get(name=request.data.get("platform"))
                
                if platform_instance.name == "Facebook":
                    page_instance = FacebookPageModel.objects.get(facebook_page_id=request.data.get("page_id"))
                    data = request.data.copy()
                    
                    data["platform"] = platform_instance.pk
                    data["social_media_account"] = page_instance.social_media_account.pk
                    serializer = PostSerializer(data=data, context={'request': request, "get_posts_page": "post"})
                    saved_posts = []

                    if serializer.is_valid():
                        access_token = page_instance.facebook_page_access_token
                        facebook_data = FacebookService.get_facebook_posts(access_token, page_instance.facebook_page_id)

                        for post_data in facebook_data.get("data", []):
                            prepared_data = prepare_facebook_post_data(post_data, page_instance, platform_instance)
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
                    data = request.data.copy()
                    page_instance =InstagramModel.objects.get(instagram_id=request.data.get("page_id"))
                    
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
                        # return create_response(
                        #     message=data,
                        #     status_code=status.HTTP_400_BAD_REQUEST
                        # ) 

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



    # @decorators.action(methods=["post"], detail=False, url_path="publish")
    # def publish(self, request):
    #     """
    #     Publish posts to specified platforms based on external_page_id.

    #     Args:
    #         request (Request): The request object containing:
    #             - page_ids (list): List of external_page_ids to publish to.
    #             - post_data (dict): Data of the post to be published.

    #     Returns:
    #         Response: A response indicating success or failure.
    #     """
    #     user_instance = get_user_from_token(request=request)
    #     try:
    #         # التحقق من أن المستخدم لديه صلاحية النشر
    #         if not user_instance.manager is None:
    #             user_instance = user_instance.manager

    #         # الحصول على قائمة page_ids من request.data
    #         page_ids = request.data.get("page_ids", [])
    #         if not page_ids:
    #             return create_response(
    #                 errors="error",
    #                 message="No page_ids provided.",
    #                 status_code=status.HTTP_400_BAD_REQUEST
    #             )

    #         # الحصول على الحسابات الاجتماعية المرتبطة بـ page_ids
    #         social_accounts = SocialMediaAccount.objects.filter(
    #             Q(user=user_instance) & Q(external_account_id__in=page_ids))
            
    #         # فصل الصفحات حسب المنصة
    #         facebook_pages = []
    #         instagram_pages = []
    #         for account in social_accounts:
    #             if account.platform.name == "Facebook":
    #                 facebook_pages.append(account.external_account_id)
    #             elif account.platform.name == "Instagram":
    #                 instagram_pages.append(account.external_account_id)

    #         # تنفيذ النشر على فيسبوك
    #         if facebook_pages:
    #             for page_id in facebook_pages:
    #                 try:
    #                     # الحصول على صفحة الفيسبوك
    #                     facebook_page = FacebookPageModel.objects.get(facebook_page_id=page_id)
    #                     # تنفيذ النشر باستخدام FacebookService
    #                     # FacebookService.publish_post(
    #                     #     access_token=facebook_page.facebook_page_access_token,
    #                     #     page_id=page_id,
    #                     #     post_data=request.data.get("post_data", {}))
                        
    #                 except Exception as e:
    #                     return create_response(
    #                         errors="error",
    #                         message=f"Failed to publish to Facebook page {page_id}: {e}",
    #                         status_code=status.HTTP_400_BAD_REQUEST
    #                     )

    #         # تنفيذ النشر على إنستقرام
    #         if instagram_pages:
    #             for page_id in instagram_pages:
    #                 try:
    #                     # الحصول على صفحة الإنستقرام
    #                     instagram_page = InstagramModel.objects.get(instagram_page_id=page_id)
    #                     # تنفيذ النشر باستخدام InstagramService
    #                     # InstagramService.publish_post(
    #                     #     access_token=instagram_page.instagram_page_access_token,
    #                     #     page_id=page_id,
    #                     #     post_data=request.data.get("post_data", {}))
    #                 except Exception as e:
    #                     return create_response(
    #                         errors="error",
    #                         message=f"Failed to publish to Instagram page {page_id}: {e}",
    #                         status_code=status.HTTP_400_BAD_REQUEST
    #                     )

    #         # إرجاع رسالة نجاح
    #         return create_response(
    #             message="Posts published successfully.",
    #             status_code=status.HTTP_200_OK
    #         )
    #     except (BaseException, ValidationError, HttpResponse) as e:
    #         return create_response(
    #             errors="error",
    #             message=str(e),
    #             status_code=status.HTTP_400_BAD_REQUEST
    #         )
        

    @decorators.action(methods=["post"], detail=False, url_path="publish")
    def publish(self, request):
        user_instance = get_user_from_token(request=request)
        try:
            # التحقق من أن المستخدم لديه صلاحية النشر
            if not user_instance.manager is None:
                user_instance = user_instance.manager

            # الحصول على قائمة page_ids من request.data
            page_ids = request.data.get("page_ids", [])
            print(f"Request Data: {request.data}")
            print(f"Page IDs (from request): {page_ids}")
            print(f"Type of Page IDs: {type(page_ids)}")

            # إذا كانت page_ids سلسلة نصية، قم بتحويلها إلى قائمة
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

            # التحقق من أن page_ids هي قائمة
            if not isinstance(page_ids, list):
                return create_response(
                    errors="error",
                    message="page_ids must be a list.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # التحقق من أن page_ids هي سلاسل نصية
            page_ids = [str(page_id) for page_id in page_ids]
            print(f"Page IDs (as strings): {page_ids}")

            # الحصول على الحسابات الاجتماعية المرتبطة بـ page_ids
            print(page_ids)

            social_accounts = SocialMediaAccount.objects.filter(
                Q(user=user_instance) & Q(external_account_id__in=page_ids)
            )

            # طباعة الحسابات الاجتماعية للتحقق
            print(f"Social Accounts: {social_accounts}")

            # إذا لم يتم العثور على حسابات اجتماعية
            if not social_accounts:
                return create_response(
                    errors="error",
                    message="No social accounts found for the provided page_ids.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # تجميع الصفحات حسب المنصة
            grouped_pages = {
                platform: list(pages)
                for platform, pages in groupby(
                    sorted(social_accounts, key=attrgetter("platform.name")),
                    key=attrgetter("platform.name")
                )
            }

            # طباعة الصفحات المجمعة للتحقق
            print(f"Grouped Pages: {grouped_pages}")
            print(f"post_data : {request.data.get("post_data", {})}")

            # تنفيذ النشر بشكل غير متزامن
            asyncio.run(self.publish_async(grouped_pages, request.data.get("post_data", {})))

            # إرجاع رسالة نجاح
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



    async def publish_async(self, grouped_pages, post_data):
        """
        تنفيذ النشر بشكل غير متزامن.
        """
        for platform, page_ids in grouped_pages.items():
            for page_id in page_ids:
                try:
                    print(page_id)
                    if platform == "Facebook":
                        page = await sync_to_async(FacebookPageModel.objects.get)(social_media_account=page_id)
                        post = await sync_to_async(FacebookService.post)(
                            access_token=page.facebook_page_access_token,
                            page_id=page.facebook_page_id,
                            post_message=post_data.get("content",""),
                            image_path=post_data.get("media_url",""),
                            # link=post_data.get("media_url",""),
                            at_time=post_data.get("scheduled_at",""),
                        )
                    elif platform == "Instagram":
                        pass
                        # page = await sync_to_async(InstagramModel.objects.get)(instagram_page_id=page_id)
                        # await sync_to_async(InstagramService.publish_post)(
                        #     access_token=page.instagram_page_access_token,
                        #     page_id=page_id,
                        #     post_data=post_data
                        # )
                except Exception as e:
                    raise ValueError(f"Failed to publish to {platform} page {page_id}: {e}")

async def publish_to_platform_async(platform, page_ids, post_data):
        """
        تنفيذ النشر على منصة معينة بشكل غير متزامن.
        """
        tasks = []
        for page_id in page_ids:
            try:
                if platform == "Facebook":
                    page = await sync_to_async(FacebookPageModel.objects.get(facebook_page_id=page_id))
                    tasks.append(asyncio.create_task(
                        FacebookService.post(
                        access_token=page.facebook_page_access_token,
                        page_id=page_id,
                        post_message=post_data.get("content",""),
                        image_path=post_data.get("media_url",""),
                        # link=post_data.get("media_url",""),
                        at_time=post_data.get("scheduled_at",""),
                    )))
                elif platform == "Instagram":
                    pass
                    # page = InstagramModel.objects.get(instagram_page_id=page_id)
                    # tasks.append(asyncio.create_task(InstagramService.publish_post_async(
                    #     access_token=page.instagram_page_access_token,
                    #     page_id=page_id,
                    #     post_data=post_data
                    # )))
            except Exception as e:
                raise ValueError(f"Failed to publish to {platform} page {page_id}: {e}")

        await asyncio.gather(*tasks)

async def publish_async(grouped_pages, post_data):
        """
        تنفيذ النشر على جميع المنصات بشكل غير متزامن.
        """
        tasks = []
        for platform, page_ids in grouped_pages.items():
            tasks.append(asyncio.create_task(publish_to_platform_async(platform, page_ids, post_data)))
            
        await asyncio.gather(*tasks)


