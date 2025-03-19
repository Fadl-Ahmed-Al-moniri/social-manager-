from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from user.models import UserModel
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def send_email_message(user, reverse_viewname, title, content):
    try:
        validate_email(user.email)
        print(validate_email(user.email))
    except ValidationError:
        raise ValueError(f"Invalid email address: {user.email}")

    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id))
        verification_url = settings.FRONTEND_URL + reverse(reverse_viewname, args=[uid, token])
        print(f"verification_url   {verification_url}")

        subject = title
        message = f'{content}: {verification_url}'
        print(f"message   {message}")

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        print(f"recipient_list   {user.email}")

        sendmail = send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list, fail_silently=True)
        print(f"sendmail         {sendmail}")
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist) as m:
        raise ValueError(f"send_email_message_error: {m}")