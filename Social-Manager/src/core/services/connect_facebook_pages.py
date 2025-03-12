from platform_media.models import FacebookPageModel
from platform_media.serializers import FacebookPageModelSerializer
from rest_framework import serializers
from core.services.facebook_services import FacebookService
from core.services.create_response import create_response
from accounts_connection.models import SocialMediaAccount



def connect_facebook_pages(userinfo,user_access_token, facebook_user_model, page_ids , platform_facebook):
    try:
        if not page_ids:
            raise serializers.ValidationError("It's required to have pages in this account.")

        data = FacebookService.fetch_facebook_user_pages(user_access_token)
        print("FacebookService.fetch_facebook_user_pages(user_access_token)")
        pages_data = data.get("accounts", {}).get("data", [])
        print(f"page_ids  {page_ids}")
        print(f"pages_data  {pages_data}")
        saved_pages = []

        for page in pages_data:
            if page["id"] in page_ids:
                print("if page[id] in page_ids:")

                if FacebookPageModel.objects.filter(facebook_page_id=page["id"]).exists():
                    raise serializers.ValidationError(f"This page {page['name']} has already been connected.")
                print(facebook_user_model.social_media_account)
                social_account, created = SocialMediaAccount.objects.get_or_create(
                user=userinfo, platform=platform_facebook ,
                external_account_id=page["id"] ,
                account_name = page["name"]
                )

                page_data = {
                    "social_media_account": social_account.pk,
                    "facebook_user": facebook_user_model.pk,
                    "facebook_page_id": page["id"],
                    "facebook_page_name": page["name"],
                    "global_name_brand": page.get("global_brand_page_name", ""),
                    "facebook_page_access_token": page["access_token"],
                    "facebook_page_picture_url": page["picture"]["data"]["url"],
                    "followers_count": page.get("followers_count", 0),
                    "following_count": page.get("fan_count", 0),
                    "tasks": page.get("tasks", []),
                    "category": page.get("category", ""),
                }

                print(f"page_data  {page_data}")

                serializer = FacebookPageModelSerializer(data=page_data, context={"view_action": "create_page", "facebook_user_model": facebook_user_model})
                
                if serializer.is_valid():
                    serializer.save()
                    saved_pages.append(serializer.data)
                else:
                    raise serializers.ValidationError(serializer.errors)
                print(f"saved_pages  {saved_pages}")
        return saved_pages
    except Exception as e:
        raise serializers.ValidationError(str(e))
    


def prepare_facebook_post_data(post_data, page_instance, platform_instance):
            """
            prepare_post_data.
            """
            prepared_data = {
                "external_post_id": post_data.pop("id"),
                "content": post_data.pop("message",""),
                "application": post_data.pop("application", {}).get("id"),
                "media_url": post_data.pop("full_picture", None),
                "scheduled_at": post_data.pop("scheduled_publish_time", None),
                "status": "published" if post_data.pop("is_published") else "draft",
                "created_at": post_data.pop("created_time"),
                "updated_at": post_data.pop("updated_time"),
                "likes_count": len(post_data.pop("likes", {}).get("data", [])),
                "comments_count": len(post_data.pop("comments", {}).get("data", [])),
                "shares_count": post_data.pop("shares", {}).get("count", 0),
                "social_media_account": page_instance.social_media_account.pk,
                "platform": platform_instance.pk,
            }
            return prepared_data

