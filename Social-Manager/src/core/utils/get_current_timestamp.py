from django.utils import timezone

def get_current_timestamp():
    return int(timezone.now().timestamp())