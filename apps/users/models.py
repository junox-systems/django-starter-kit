# apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from auditlog.registry import auditlog
from apps.core.models import BaseModel


def user_avatar_path(instance, filename):
    """Upload path for user avatars: users/user_<id>/<filename>"""
    return f"users/user_{instance.id}/{filename}"


class User(AbstractUser, BaseModel):
    """
    Custom User model. Email-based login, UUID primary key.
    Auth (social, OIDC, email verification) is managed by django-allauth.
    """

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={"unique": _("A user with that username already exists.")},
        validators=[UnicodeUsernameValidator(), MaxLengthValidator(150)],
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=254,
    )

    # Avatar — stored on User directly (idiomatic Django)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        help_text=_("User profile picture."),
    )
    avatar_thumbnail = ImageSpecField(
        source="avatar",
        processors=[ResizeToFill(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        self.username = self.username.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


# Register with django-auditlog for automatic change tracking
auditlog.register(User)
