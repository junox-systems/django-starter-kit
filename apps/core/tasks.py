# apps/core/tasks.py
#
# Background task examples. Every task is a @dramatiq.actor; enqueue with
# `task.send(*args)` from anywhere (views, signals, management commands).
# Workers run in the `worker` container / `python manage.py rundramatiq`.

import dramatiq

from django.conf import settings
from django.core.mail import send_mail

from apps.users.models import User


@dramatiq.actor
def send_welcome_email(user_id):
    """Send a welcome email after signup. Example: User post_save signal."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    send_mail(
        subject="Welcome aboard",
        message=f"Hi {user.username}, thanks for signing up.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


@dramatiq.actor(max_retries=5, min_backoff=1000, max_backoff=30000)
def export_user_data(user_id):
    """Example long-running job: build an export artifact for a user.

    Uses default retry middleware — failures back off up to 30s, 5 tries.
    """
    user = User.objects.get(id=user_id)
    # ... build the export ...
    return f"exports/user_{user.id}.csv"


@dramatiq.actor
def send_test_email(subject, message, recipient_list):
    """Send a test email (used by admin checks / debugging)."""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
    )
