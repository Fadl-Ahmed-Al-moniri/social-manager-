from datetime import datetime
import time
from typing import Any, Dict, Optional
from rest_framework.exceptions import ValidationError
from pyfacebook.api import GraphAPI


class InstgramService:
    """
    A service to deal with Instgram, including verification and fetching data.
    """


    @staticmethod
    def fetch_instagram_business_user_info(user_access_token, instagram_id):
        """
        Fetch Instagram business account details using the Instagram ID.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            instagram_data = api.get_object(
                object_id=instagram_id,
                fields="id,name,username,profile_picture_url,followers_count,follows_count"
            )
            return instagram_data
        except Exception as e:
            raise ValueError(f"Error fetching Instagram business account data: {e}")

    @staticmethod
    def validate_instgram_business_account(user_access_token, instagram_id):
            """
            Check the authenticity of the token and user ID on Instgram.
            """
            try:
                api = GraphAPI(access_token=user_access_token)
                user_data = api.get_object(object_id=instagram_id, fields="id")
                
                if user_data : 
                    return True
                if str(user_data["id"]) != instagram_id:
                    raise ValidationError("instagram_id does not match the token's user.")
            except Exception as e:
                raise ValidationError(f"Error validating Facebook account: {e}")

    @staticmethod
    def fetch_instagram_user_info(user_access_token):
        """
        Fetch data for the user account linked to your Instagram account via Facebook authentication.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            data = api.get_object(
                object_id="me",
                fields=r"id,name,picture{url},accounts{id,name,global_brand_page_name,picture{url},access_token,category,followers_count,fan_count,instagram_business_account}"
            )

            pages_data = data.get("accounts", {}).get("data", [])
            saved_pages = []

            for page in pages_data:
                # التحقق من وجود instagram_business_account
                instagram_account = page.get("instagram_business_account")
                if instagram_account and instagram_account.get("id"):
                    instagram_id = instagram_account["id"]
                    instagram_data =InstgramService.fetch_instagram_business_user_info(user_access_token, instagram_id)

                    # تجميع البيانات
                    page_data = {
                        "user": {
                            "name": data.get("name"),
                            "picture": data.get("picture", {}).get("data", {}).get("url", "")
                        },
                        "page": {
                            "facebook_page_id": page.get("id"),
                            "facebook_page_name": page.get("name"),
                            "global_name_brand": page.get("global_brand_page_name", ""),
                            "facebook_page_access_token": page.get("access_token"),
                            "facebook_page_picture_url": page.get("picture", {}).get("data", {}).get("url", ""),
                            "followers_count": page.get("followers_count", 0),
                            "following_count": page.get("fan_count", 0),
                            "category": page.get("category", "")
                        },
                        "instagram_business_account": {
                            "id": instagram_data.get("id"),
                            "name": instagram_data.get("name"),
                            "username": instagram_data.get("username"),
                            "profile_picture_url": instagram_data.get("profile_picture_url"),
                            "followers_count": instagram_data.get("followers_count", 0),
                            "follows_count": instagram_data.get("follows_count", 0)
                        }
                    }
                    saved_pages.append(page_data)

            return saved_pages

        except Exception as e:
            raise ValueError(f"Error fetching pages data: {e}")
        

    @staticmethod
    def get_media_ids(user_access_token , page_id):
        """
        Fetch data for the user account linked to your Instagram account via Facebook authentication.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            data = api.get_object(
                object_id=page_id,
                fields=f"media"
            )

            id_s =  []
            for media_id in data.get("media",{}).get("data",[]) :
                id_s.append(media_id.get("id",""))
            return id_s
        except Exception as e:
            raise ValueError(f"Error fetching media data: {e}")
        

    @staticmethod
    def get_media_info(user_access_token, page_id, platform_instance: Optional[str] = None , page_instance : Optional[str] = None  ,created_at : Optional[str] = None ):
        """
        Fetch data for the user account linked to your Instagram account via Facebook authentication.

        Args:
            user_access_token (str): The access token for the user to authenticate with Facebook API.
            page_id (str): The ID of the Facebook page to fetch media data from.

        Returns:
            list: A list of dictionaries containing media information. Each dictionary contains:
                - external_post_id (str): The ID of the media post.
                - content (str): The caption or text associated with the media.
                - media_url (str): The URL of the media (image or video).
                - created_at (str): The timestamp when the media was created.
                - likes_count (int): The number of likes on the media.
                - comments_count (int): The number of comments on the media.

        Raises:
            ValueError: If an error occurs while fetching media data.
        """
        try:
            # Initialize the Facebook Graph API
            api = GraphAPI(access_token=user_access_token)

            # Fetch media IDs from the page
            data = api.get_object(
                object_id=page_id,
                fields="media"
            )

            # Extract media IDs
            id_s = []
            for media_id in data.get("media", {}).get("data", []):
                id_s.append(media_id.get("id", ""))

            # Fetch detailed information for each media
            media_info = []
            for id in id_s:
                media = api.get_object(
                    object_id=id,
                    fields="id,caption,media_url,thumbnail_url,timestamp,like_count,comments_count"
                )
                dt = datetime.strptime(media["timestamp"], r"%Y-%m-%dT%H:%M:%S%z")
                info = {
                    "social_media_account": page_instance.social_media_account.pk,
                    "platform": platform_instance.pk,
                    "external_post_id": media.get("id", ""),
                    "content": media.get("caption", ""),
                    "media_url": media.get("media_url") or media.get("thumbnail_url"),
                    "created_at": int(time.mktime(dt.timetuple())),
                    "likes_count": media.get("like_count", 0),
                    "comments_count": media.get("comments_count", 0),
                }
                media_info.append(info)

            return media_info

        except Exception as e:
            # Raise an error if something goes wrong
            raise ValueError(f"Error fetching media data: {e}")
        


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

