# apps/core/models.py

import uuid
from uuid_utils import uuid7
from django.db import models


def uuid7_default():
    return uuid.UUID(bytes=uuid7().bytes)


class BaseModel(models.Model):
    """
    Abstract base model with UUID v7 primary key and timestamps.
    UUID v7 (RFC 9562) is time-ordered, which gives much better B-tree
    index performance compared to random UUID v4.
    """

    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
