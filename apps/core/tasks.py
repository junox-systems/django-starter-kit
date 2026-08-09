# apps/core/tasks.py
#
# Background task examples. Every task is a @shared_task; enqueue with
# `task.delay(*args)` or `task.apply_async(args, countdown=...)` from anywhere
# (views, signals, management commands).
# Workers run in the `worker` container / `celery -A config worker`.

import smtplib

import anymail.exceptions
from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail
from django.db import OperationalError

from apps.users.models import User


@shared_task(
    autoretry_for=(
        smtplib.SMTPException,
        anymail.exceptions.AnymailAPIError,
        OSError,
        TimeoutError,
    ),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=30,
)
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


@shared_task(
    autoretry_for=(OperationalError, TimeoutError),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=30,
)
def export_user_data(user_id):
    """Example long-running job: build an export artifact for a user.

    Retries with exponential backoff up to 30s, 5 tries.
    """
    user = User.objects.get(id=user_id)
    # ... build the export ...
    return f"exports/user_{user.id}.csv"


@shared_task(
    autoretry_for=(
        smtplib.SMTPException,
        anymail.exceptions.AnymailAPIError,
        OSError,
        TimeoutError,
    ),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=30,
)
def send_test_email(subject, message, recipient_list):
    """Send a test email (used by admin checks / debugging)."""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
    )
