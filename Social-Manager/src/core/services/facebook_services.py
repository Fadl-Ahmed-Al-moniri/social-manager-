from typing import Any, Dict, Optional
from rest_framework.exceptions import ValidationError
from pyfacebook.api import GraphAPI
from datetime import datetime
import time
from django.conf import settings
import requests
import os

class FacebookService:
    """
    A service to deal with Facebook, including verification and fetching data.
    """

    @staticmethod
    def validate_facebook_account(user_access_token, facebook_user_id):
        """
        Check the authenticity of the token and user ID on Facebook.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            user_data = api.get_object(object_id="me", fields="id")
            if str(user_data["id"]) != facebook_user_id:
                raise ValidationError("facebook_user_id does not match the token's user.")
        except Exception as e:
            raise ValidationError(f"Error validating Facebook account: {e}")

    @staticmethod
    def fetch_facebook_user_data(user_access_token):
        """
        Fetch user data from Facebook.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            user_data = api.get_object(
                object_id="me",
                fields="id,name,picture,email"
            )
            return user_data
        except Exception as e:
            raise ValueError(f"Error fetching user data: {e}")

    @staticmethod
    def fetch_facebook_user_pages(user_access_token):
        """
        Fetch data for pages associated with your Facebook account.
        """
        try:
            api = GraphAPI(access_token=user_access_token)
            pages_data = api.get_object(
                object_id="me",
                fields=r"accounts{id,name,global_brand_page_name,picture{url},access_token,category,followers_count,fan_count,tasks}"
            )
            return pages_data
        except Exception as e:
            raise ValueError(f"Error fetching pages data: {e}")
        
    @staticmethod
    def fetch_facebook_user_info(user_access_token ):
        """
        Fetch data for account of user associated with your Facebook account.
        """
        try:
            api = GraphAPI(access_token=user_access_token, )
            data = api.get_object(
                object_id="me",
                fields=r"id,name,picture{url},accounts{id,name,global_brand_page_name,picture{url}}"
            )
            return data
        except Exception as e:
            raise ValueError(f"Error fetching pages data: {e}")
    
    @staticmethod
    def get_long_lived_access_token(short_lived_access_token):
        """
            Get a long-term access token from Facebook.

            :p aram short_lived_access_token: short-term access token.
            :return: Long-term access token or None in case of failure.
        """

        url = fr"https://graph.facebook.com/{settings.FACEBOOK_GRAPH_API_VERSION}/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'fb_exchange_token': short_lived_access_token,
        }

        try:

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching long-lived access token: {e}")
            return None
    
    
    
    @staticmethod
    def post(
            access_token: str, 
            page_id: str, 
            post_message: str, 
            at_time: Optional[str] = None, 
            image_path: Optional[str] = None,
            link: Optional[str] = None
            ): 
                
                """
                This function is for posting on Facebook with support for multiple cases e.g: scheduling status, attaching a picture, or posting at the moment
                
                :param access_token: Token access with the necessary permissions.
                :param page_id: Page ID.
                :param post_message: Content of the post.
                :param image_path: Local image path if any.
                :param at_time: Unix timestamp for scheduling the post.
                :param link: Optional link to include in the post.
                """
                # Initialize the Facebook Graph API
                graph = GraphAPI(access_token=access_token)

                # Ensure `at_time` is a valid Unix timestamp if provided
                if at_time:
                    try:
                        at_time = int(at_time)
                    except ValueError:
                        raise ValueError("The 'at_time' parameter must be a valid Unix timestamp.")

                # Prepare parameters for the post
                params = {
                    "message": post_message,
                    "link": link,
                    "scheduled_publish_time": at_time,
                    "published": "false" if at_time else "true",
                }


                if image_path[0].startswith("http"):
                    print(image_path[0].startswith("http"))
                    try:
                        params["url"] = image_path[0]
                        response = graph.post_object(
                            object_id=page_id,
                            connection="photos",
                            params=params,
                        )
                        return response

                    except Exception as e:
                        raise RuntimeError(f"An error occurred while uploading the photo: {e}")
                elif not image_path[0].startswith("http"):
                    try:
                        with open(image_path[0], 'rb') as image_file:
                            files = {'source': image_file}  # Attach the image file
                            response = graph.post_object(
                                object_id=page_id,
                                connection="photos",
                                params=params,
                                files=files
                            )
                        return response
                    except FileNotFoundError as e:
                        raise FileNotFoundError(f"Image file not found: {e}")
                    except Exception as e:
                        raise RuntimeError(f"An error occurred while uploading the photo: {e}")

                try:
                    response = graph.post_object(
                        object_id=page_id,
                        connection="feed",
                        params=params
                    )

                    return response
                except Exception as e:
                    raise RuntimeError(f"An error occurred while posting: {e}")

    @staticmethod
    def post_reel_to_page(
        access_token: str,
        page_id: str,
        video_path: str,
        description: Optional[str] = None,
        scheduled_publish_time: Optional[int] = None,
        place_id: Optional[str] = None,
        max_retries: int = 30,  # عدد المحاولات للتحقق من الحالة
        retry_interval: int = 4,  # الفترة بين المحاولات (بالثواني)
    ):
        """
        This function is for posting a Reel on a Facebook Page and waits until it is published.

        :param access_token: Token access with the necessary permissions.
        :param page_id: Page ID.
        :param video_path: Local path or URL of the video file.
        :param description: Optional description for the Reel.
        :param scheduled_publish_time: Unix timestamp for scheduling the Reel.
        :param place_id: Optional place ID to tag a location in the Reel.
        :param max_retries: Maximum number of retries to check the video status.
        :param retry_interval: Time interval between retries (in seconds).
        :return: Response from the Facebook Graph API.
        """
        # Initialize the Facebook Graph API
        graph = GraphAPI(access_token=access_token )

        try:
            # Step 1: Initialize an upload session
            upload_session = graph.post_object(
                object_id=page_id,
                connection="video_reels",
                params={
                    "upload_phase": "start",
                    "access_token": access_token,
                },
            )

            print(upload_session)

            video_id = upload_session.get("video_id")
            upload_url = upload_session.get("upload_url")

            print(video_id)
            print(upload_url)

            if not video_id or not upload_url:
                raise RuntimeError("Failed to initialize upload session.")

            # Step 2: Upload the video
            if video_path.startswith("https"):
                # Upload from a URL
                print("https")
                upload_params = {
                    "Authorization": f"OAuth {access_token}",
                    "file_url": video_path,
                }
                upload_response = requests.post(upload_url, headers=upload_params)

            else:
                # Upload from a local file
                with open(video_path, "rb") as video_file:
                    files = {"source": video_file}
                    upload_response = requests.post(
                        upload_url,
                        files=files,
                        headers={"Authorization": f"OAuth {access_token}"},
                    )

            print(upload_response)
            print("upload_response")

            upload_response.raise_for_status()
            upload_data = upload_response.json()

            if not upload_data.get("success"):
                raise RuntimeError("Failed to upload the video.")

            # Step 3: Wait for the video to be ready
            status_url = f"https://graph.facebook.com/v22.0/{video_id}"
            status_params = {
                "fields": "status",
                "access_token": access_token,
            }

            retries = 0
            while retries < max_retries:
                status_response = requests.get(status_url, params=status_params)
                status_response.raise_for_status()
                status_data = status_response.json()

                video_status = status_data.get("status", {}).get("video_status")
                print(video_status)
                print("video_status")
                if video_status == "ready":
                    break  # الفيديو جاهز للنشر
                if video_status == "upload_complete":
                    break  # الفيديو جاهز للنشر
                elif video_status == "processing":
                    print(f"Video is still processing. Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                    retries += 1
                else:
                    raise RuntimeError(f"Unexpected video status: {video_status}")

            if retries >= max_retries:
                raise RuntimeError("Video processing took too long. Please try again later.")

            # Step 4: Publish the Reel
            publish_params = {
                "upload_phase": "finish",
                "video_id": video_id,
                "video_state": "PUBLISHED",
                "description": description,
                "scheduled_publish_time": scheduled_publish_time,
                "place": place_id,
                "access_token": access_token,
            }

            publish_response = graph.post_object(
                object_id=page_id,
                connection="video_reels",
                params=publish_params,
            )
            if publish_response["success"] ==True:
                response = graph.get_object(object_id=video_id,fields="permalink_url")
                url =f"https://www.facebook.com{response["permalink_url"]}"
                publish_response["video_url"] = url
            publish_response["video_id"] = video_id
            return publish_response 

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"An error occurred while posting the Reel: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")



    @staticmethod 
    def update_post(access_token: str, page_post_id: str, post_message: str):
        """
        Updates a Facebook post with new content.

        :param access_token: Access token with the necessary permissions.
        :param page_post_id: The ID of the post to be updated.
        :param post_message: The new message content for the post.
        :return: A success message or raises an error if the update fails.
        """


        # Initialize the Facebook Graph API
        graph = GraphAPI(access_token=access_token)

        # Parameters for the update
        params = {
            "message": post_message,
        }

        try:
            # Update the post
            response = graph.post_object(
                    object_id=page_post_id,
                    params=params
                )

            # Check if the response indicates success
            if response.get("success", False):
                return response
            else:
                raise RuntimeError(f"Failed to update the post: {response}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while updating the post: {e}")
        
    @staticmethod
    def delete_post(access_token: str, post_id: str):
        """
        Deletes a Facebook post by its ID.

        :param access_token: Access token with the necessary permissions.
        :param post_id: The ID of the post to be deleted.
        :return: A success message if the post is deleted, raises an error otherwise.
        """

        # Initialize the Facebook Graph API
        graph = GraphAPI(access_token=access_token)

        try:
            # Make the API call to delete the post
            response = graph.delete_object(object_id=post_id)

            # Check if the operation was successful
            if response.get("success", False):
                return f"Post with ID {post_id} deleted successfully."
            else:
                raise RuntimeError(f"Failed to delete the post with ID {post_id}. Response: {response}")

        except Exception as e:
            raise RuntimeError(f"An error occurred while deleting the post: {e}")
    @staticmethod
    def get_facebook_posts(access_token: str, page_id: str, fields: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch posts from a Facebook page using its ID.

        :param access_token: The access token with the required permissions.
        :param page_id: The ID of the Facebook page.
        :param fields: Comma-separated list of fields to fetch. Defaults to commonly used fields.
        :param limit: Maximum number of posts to fetch. Default is 10.
        :return: A dictionary containing the posts' data.
        :raises RuntimeError: If an error occurs during the API call.
        """
        if not access_token or not page_id:
            raise ValueError("Access token and page ID are required.")

        # Default fields if not provided
        # fields = fields or "id,message,created_time,updated_time,from,full_picture,is_published,shares,permalink_url,status_type,likes"
        fields = fields or r"id,application{id},message,message_tags,scheduled_publish_time,is_published,created_time,updated_time,promotion_status,status_type,full_picture,from,likes,comments"

        # Initialize the Facebook Graph API
        graph = GraphAPI(access_token=access_token)

        try:
            # Fetch posts with optional pagination
            posts = graph.get_object(
                f"{page_id}/posts", 
                fields=fields, 
                limit=limit
            )

            for post in posts.get("data", []):
                if "created_time" in post:
                    dt = datetime.strptime(post["created_time"], r"%Y-%m-%dT%H:%M:%S%z")
                    post["created_time"] = int(time.mktime(dt.timetuple()))
                if "updated_time" in post:
                    dt = datetime.strptime(post["updated_time"], r"%Y-%m-%dT%H:%M:%S%z")
                    post["updated_time"] = int(time.mktime(dt.timetuple()))
                if "scheduled_publish_time" in post:
                    dt = datetime.strptime(post["scheduled_publish_time"], r"%Y-%m-%dT%H:%M:%S%z")
                    post["scheduled_publish_time"] = int(time.mktime(dt.timetuple()))
            print(posts)
            return posts

        except Exception as e:
            raise RuntimeError(f"Failed to fetch posts for page {page_id}: {e}")

    @staticmethod
    def get_info_post(access_token: str, post_id: str, fields: Optional[str] = None) -> dict:
        """
        Fetch detailed information about a specific Facebook post using its ID.

        :param access_token: The access token with the required permissions.
        :param post_id: The ID of the post to retrieve information for.
        :param fields: Comma-separated list of fields to fetch. Defaults to commonly used fields.
        :return: A dictionary containing the post's details.
        :raises RuntimeError: If an error occurs while fetching the post.
        """
        if not access_token or not post_id:
            raise ValueError("Access token and post ID are required and cannot be empty.")

        # Initialize the Facebook Graph API
        graph = GraphAPI(access_token=access_token)

        # Default fields if not provided
        fields = fields or "id,message,created_time,updated_time,likes,full_picture,is_published,shares,permalink_url,status_type,attachments"

        try:
            # Make the API call
            post_info = graph.get_object(object_id=post_id, fields=fields)

            return post_info

        except Exception as e:
            print(f"Error occurred while fetching post ID {post_id}: {e}")
            raise RuntimeError(f"An error occurred while fetching the post: {e}")


