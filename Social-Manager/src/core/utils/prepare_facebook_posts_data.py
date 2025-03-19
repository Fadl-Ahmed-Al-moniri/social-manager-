
def prepare_facebook_posts_data(post_data, page_instance, platform_instance):
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
