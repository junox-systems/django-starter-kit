from django.conf import settings
from django.core.mail import send_mail

from apps.core.tasks import EMAIL_ERRORS, retry

from .models import Invitation


@retry(*EMAIL_ERRORS)
def send_invitation_email(invitation_id, accept_url):
    try:
        invitation = Invitation.objects.select_related("organization").get(
            id=invitation_id
        )
    except Invitation.DoesNotExist:
        return  # revoked before the worker got to it
    send_mail(
        subject=f"You're invited to join {invitation.organization}",
        message=f"Accept the invitation: {accept_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
    )
