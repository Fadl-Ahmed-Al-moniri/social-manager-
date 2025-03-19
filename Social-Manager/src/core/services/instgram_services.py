from datetime import datetime
import time
from rest_framework.exceptions import ValidationError
from pyfacebook.api import GraphAPI
from typing import Optional, List, Dict, Union



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
    
    
    
    @staticmethod
    def publish_post_to_instagram(
        access_token: str,
        page_user_id: str,
        media_urls: List[str],
        caption: str,
        user_tags: Optional[List[Dict[str, Union[str, float]]]] = None,
        media_type: str = "IMAGE",
        location_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Publish a post to Instagram (single image/video or carousel).

        :param access_token: Token access with the necessary permissions.
        :param page_user_id: Page user ID.
        :param media_urls: List of media URLs (images or videos).
        :param caption: Content of the post.
        :param user_tags: List of user tags (e.g., [{"username": "user1", "x": 0.5, "y": 0.5}]).
        :param media_type: Type of media ("IMAGE" or "VIDEO").
        :param location_id: Location ID for tagging.
        :return: ID of the published media.
        """
        try:
            api = GraphAPI(access_token=access_token)
            children = []

            # Create media containers for each URL
            for url in media_urls:
                params = {
                    "caption": caption,
                    "user_tags": user_tags,
                    "location_id": location_id,
                }

                if len(media_urls) > 1:  # Carousel post
                    params["is_carousel_item"] = "true"

                if media_type == "IMAGE":
                    params["image_url"] = url
                elif media_type == "VIDEO":
                    params["video_url"] = url
                    params["media_type"] = "VIDEO"

                container = api.post_object(
                    object_id=page_user_id,
                    connection="media",
                    params=params,
                )
                children.append(container["id"])

            # Create carousel container if multiple media items
            if len(media_urls) > 1:
                params = {
                    "media_type": "CAROUSEL",
                    "children": children,
                    "caption": caption,
                    "user_tags": user_tags,
                    "location_id": location_id,
                }
                creation_id = api.post_object(
                    object_id=page_user_id,
                    connection="media",
                    params=params,
                )
            else:
                creation_id = {"id": children[0]}  # Single media post

            # Publish the media
            if creation_id:
                response = api.post_object(
                    object_id=page_user_id,
                    connection="media_publish",
                    params={"creation_id": creation_id["id"]},
                )
                return response

        except Exception as e:
            raise ValueError(f"Error publishing post: {e}")
    @staticmethod
    def publish_reel_to_instagram(
        access_token: str,
        page_user_id: str,
        video_url: str,
        caption: str,
        user_tags: Optional[List[Dict[str, Union[str, float]]]] = None,
        location_id: Optional[str] = None,
        max_retries: int = 20,
        wait_time: int = 30,
    ) -> Optional[str]:
        """
        Publish a Reel to Instagram with retry logic for media processing.

        :param access_token: Token access with the necessary permissions.
        :param page_user_id: Page user ID.
        :param video_url: Direct URL to the video file.
        :param caption: Content of the post.
        :param user_tags: List of user tags.
        :param location_id: Location ID for tagging.
        :param max_retries: Maximum number of retries for media processing.
        :param wait_time: Time to wait between retries (in seconds).
        :return: ID of the published Reel.
        """
        try:
            api = GraphAPI(access_token=access_token)

            # Step 1: Create media container
            params = {
                "video_url": video_url,
                "caption": caption,
                "user_tags": user_tags,
                "location_id": location_id,
                "media_type": "REELS",
            }

            creation_id = api.post_object(
                object_id=page_user_id,
                connection="media",
                params=params,
            )

            if not creation_id or "id" not in creation_id:
                raise ValueError("Failed to create media container.")

            container_id = creation_id["id"]

            # Step 2: Wait for media to be ready
            retries = 0
            while retries < max_retries:
                container_status = api.get_object(
                    object_id=container_id,
                    fields="status_code",
                )

                if container_status.get("status_code") == "FINISHED":
                    print("break")
                    break  # Media is ready
                elif container_status.get("status_code") == "ERROR":
                    raise ValueError("Media processing failed.")

                retries += 1
                print(f"Waiting for media to process... Attempt {retries}/{max_retries}")
                time.sleep(wait_time)  # Wait before retrying

            if retries >= max_retries:
                raise ValueError("Media processing timed out.")

            # Step 3: Publish the media
            response = api.post_object(
                object_id=page_user_id,
                connection="media_publish",
                params={"creation_id": container_id},
            )
            if response["id"] :
                reel_url = api.get_object(object_id=response["id"] ,access_token = access_token ,fields="media_url")

                response["video_url"] = reel_url["media_url"]
            
            return response

        except Exception as e:
            raise ValueError(f"Error publishing Reel: {e}")



    @staticmethod
    def publish_story_to_instagram(
        access_token: str,
        page_user_id: str,
        media_url: str,
        caption: str,
        user_tags: Optional[List[Dict[str, Union[str, float]]]] = None,
        media_type: str = "IMAGE",
    )-> Optional[str]:
        """
        Publish a Story to Instagram.

        :param access_token: Token access with the necessary permissions.
        :param page_user_id: Page user ID.
        :param media_url: Media URL (image or video).
        :param caption: Content of the post.
        :param user_tags: List of user tags.
        :param media_type: Type of media ("IMAGE" or "VIDEO").
        :return: ID of the published Story.
        """
        try:
            api = GraphAPI(access_token=access_token)

            params = {
                "caption": caption,
                "user_tags": user_tags,
                "media_type": "STORIES",
            }

            if media_type == "IMAGE":
                params["image_url"] = media_url
            elif media_type == "VIDEO":
                params["video_url"] = media_url

            creation_id = api.post_object(
                object_id=page_user_id,
                connection="media",
                params=params,
            )

            if creation_id:
                response = api.post_object(
                    object_id=page_user_id,
                    connection="media_publish",
                    params={"creation_id": creation_id["id"]},
                )
                return response["id"]

        except Exception as e:
            raise ValueError(f"Error publishing Story: {e}")




