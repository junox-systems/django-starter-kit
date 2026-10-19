from allauth.account.signals import user_signed_up
from django.db import transaction
from django.dispatch import receiver
from django_q.tasks import async_task


@receiver(user_signed_up)
def queue_welcome_email(request, user, **kwargs):
    # on_commit: the worker must not race the signup transaction for the row.
    transaction.on_commit(
        lambda: async_task("apps.core.tasks.send_welcome_email", user.id)
    )
