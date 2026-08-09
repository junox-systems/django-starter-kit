from celery import Celery

app = Celery("django_starter_kit")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
