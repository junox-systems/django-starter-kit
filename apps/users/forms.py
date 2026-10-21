from allauth.account.adapter import get_adapter
from allauth.account.utils import filter_users_by_username
from django import forms
from django.core.exceptions import ValidationError

from .models import User

MAX_AVATAR_BYTES = 5 * 1024 * 1024
# Thumbnailing decodes the whole image in the request; cap memory per upload.
MAX_AVATAR_PIXELS = 4096 * 4096


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "avatar"]

    def clean_username(self):
        """Same rules as allauth signup (blacklist, case-insensitive uniqueness)."""
        username = self.cleaned_data["username"]
        if "username" not in self.changed_data:
            return username
        adapter = get_adapter()
        adapter.clean_username(username, shallow=True)
        if filter_users_by_username(username).exclude(pk=self.instance.pk).exists():
            raise adapter.validation_error("username_taken")
        return username

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        # Only a new upload: the stored file may be missing, and size hits storage.
        if not avatar or "avatar" not in self.changed_data:
            return avatar
        if avatar.size > MAX_AVATAR_BYTES:
            raise ValidationError("Image must be 5 MB or smaller.")
        width, height = avatar.image.size
        if width * height > MAX_AVATAR_PIXELS:
            raise ValidationError("Image must be 4096×4096 pixels or smaller.")
        return avatar
