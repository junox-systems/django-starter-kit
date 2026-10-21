from django import forms
from django.core.exceptions import ValidationError

from .models import User

MAX_AVATAR_BYTES = 5 * 1024 * 1024


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "avatar"]

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and avatar.size > MAX_AVATAR_BYTES:
            raise ValidationError("Image must be 5 MB or smaller.")
        return avatar
