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
