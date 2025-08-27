# apps/users/models.py

import secrets
from typing import Dict, List, Union
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from apps.core.models import BaseModel
from .utils import encrypt_sensitive_data, decrypt_sensitive_data


class UserAuditLog(BaseModel):
    """
    Audit log for sensitive user operations.
    Tracks important changes to user accounts for security and compliance.
    """

    ACTION_CHOICES = [
        ("account_deactivation", "Account Deactivation"),
        ("account_reactivation", "Account Reactivation"),
        ("data_anonymization", "Data Anonymization"),
        ("consent_update", "Consent Update"),
        ("profile_update", "Profile Update"),
        ("email_change", "Email Change"),
        ("password_change", "Password Change"),
    ]

    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="audit_logs"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("User Audit Log")
        verbose_name_plural = _("User Audit Logs")
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["action"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.action} - {self.created_at}"


def user_directory_path(instance, filename):
    """
    Generate upload path for user avatar files.
    Files will be uploaded to MEDIA_ROOT/users/user_<id>/<filename>
    This helps organize user files and prevents filename conflicts.
    """
    return f"users/user_{instance.user.id}/{filename}"


class User(AbstractUser, BaseModel):
    """
    Custom User model inheriting from Django's AbstractUser and our BaseModel.
    `id` from BaseModel will override the default integer ID.
    Username, email, first_name, and last_name are inherited from AbstractUser.

    This model is designed to be:
    - Production ready with proper data lifecycle management
    - GDPR compliant with data retention and deletion capabilities
    - OIDC compatible with standard claims and django-allauth integration
    """

    # Override default username validation and help text if needed
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
        validators=[UnicodeUsernameValidator(), MaxLengthValidator(150)],
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=254,
        validators=[MaxLengthValidator(254)],
    )

    # Account Status Fields
    is_verified = models.BooleanField(
        _("verified"),
        default=False,
        help_text=_("Designates whether the user has verified their email address."),
    )
    deactivated_at = models.DateTimeField(
        _("deactivated at"),
        null=True,
        blank=True,
        help_text=_("Date and time when the user account was deactivated."),
    )

    # OIDC Standard Fields
    oidc_subject = models.CharField(
        _("OIDC subject"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("OIDC subject identifier for external identity providers."),
    )
    oidc_issuer = models.URLField(
        _("OIDC issuer"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("OIDC issuer URL for the identity provider."),
    )

    # Profile completion tracking
    profile_completed = models.BooleanField(
        _("profile completed"),
        default=False,
        help_text=_("Indicates if the user has completed their profile setup."),
    )

    # Let's use email as the primary identifier for login
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["oidc_subject"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["deactivated_at"]),
            models.Index(fields=["first_name"]),
            models.Index(fields=["last_name"]),
        ]

    def clean(self):
        """
        Custom validation for the User model.
        """
        from django.core.exceptions import ValidationError

        # Validate that username is not too long
        if self.username and len(self.username) > 150:
            raise ValidationError(_("Username must be 150 characters or fewer."))

        # Validate that email is not too long
        if self.email and len(self.email) > 254:
            raise ValidationError(_("Email must be 254 characters or fewer."))

        # Validate that first_name is not too long
        if self.first_name and len(self.first_name) > 150:
            raise ValidationError(_("First name must be 150 characters or fewer."))

        # Validate that last_name is not too long
        if self.last_name and len(self.last_name) > 150:
            raise ValidationError(_("Last name must be 150 characters or fewer."))

        super().clean()

    def save(self, *args, **kwargs):
        # Normalize the email address
        self.email = self.email.lower().strip()
        # Normalize the username
        self.username = self.username.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def get_full_name_oidc(self) -> str:
        """
        Return the full name, with a fallback to username for OIDC compatibility.
        This method aligns with OIDC standard claims.
        """
        full_name = super().get_full_name()
        return full_name if full_name else self.username

    def deactivate_account(
        self, ip_address: str | None = None, user_agent: str | None = None
    ) -> None:
        """
        Deactivate the user account with audit logging.

        Args:
            ip_address (str, optional): IP address of the request
            user_agent (str, optional): User agent of the request
        """
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=["is_active", "deactivated_at"])

        # Create audit log entry
        UserAuditLog.objects.create(
            user=self,
            action="account_deactivation",
            details={
                "deactivated_at": self.deactivated_at.isoformat(),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def reactivate_account(
        self, ip_address: str | None = None, user_agent: str | None = None
    ) -> None:
        """
        Reactivate the user account with audit logging.

        Args:
            ip_address (str, optional): IP address of the request
            user_agent (str, optional): User agent of the request
        """
        self.is_active = True
        self.deactivated_at = None
        self.save(update_fields=["is_active", "deactivated_at"])

        # Create audit log entry
        UserAuditLog.objects.create(
            user=self,
            action="account_reactivation",
            details={
                "reactivated_at": timezone.now().isoformat(),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def anonymize_data(
        self, ip_address: str | None = None, user_agent: str | None = None
    ) -> None:
        """
        Anonymize user data for privacy protection while maintaining record integrity.
        This is useful for GDPR right to erasure requests where full deletion isn't possible.

        Args:
            ip_address (str, optional): IP address of the request
            user_agent (str, optional): User agent of the request
        """
        # Generate a cryptographically secure random identifier for anonymization
        anon_id = f"anon_{secrets.token_urlsafe(16)}"

        # Store original data for audit log
        original_data = {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

        # Anonymize personal data
        self.username = anon_id[:150]  # Ensure it fits in the field
        self.first_name = "Anonymous"
        self.last_name = "User"
        self.email = f"{anon_id[:50]}@anonymous.local"  # Ensure it fits in the field
        self.is_verified = False
        self.profile_completed = False

        # Clear OIDC identifiers
        self.oidc_subject = None
        self.oidc_issuer = None

        # Update timestamps
        self.updated_at = timezone.now()
        self.save(
            update_fields=[
                "username",
                "first_name",
                "last_name",
                "email",
                "is_verified",
                "profile_completed",
                "oidc_subject",
                "oidc_issuer",
                "updated_at",
            ]
        )

        # Create audit log entry
        UserAuditLog.objects.create(
            user=self,
            action="data_anonymization",
            details={
                "original_data": original_data,
                "anonymized_at": self.updated_at.isoformat(),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_data_export(self) -> Dict[str, Union[str, bool, None]]:
        """
        Return a dictionary of all user data for GDPR data export requests.
        This method provides a comprehensive view of all personal data stored.
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "date_joined": self.date_joined.isoformat() if self.date_joined else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "deactivated_at": self.deactivated_at.isoformat()
            if self.deactivated_at
            else None,
            "oidc_subject": self.oidc_subject,
            "oidc_issuer": self.oidc_issuer,
            "profile_completed": self.profile_completed,
            "created_at": self.created_at.isoformat()
            if hasattr(self, "created_at")
            else None,
            "updated_at": self.updated_at.isoformat()
            if hasattr(self, "updated_at")
            else None,
        }

    def update_oidc_claims(self, claims: Dict[str, Union[str, bool]]) -> None:
        """
        Update user fields based on OIDC claims from an identity provider.
        This method helps synchronize user data with external IDPs.

        Args:
            claims (dict): Dictionary of OIDC claims from the identity provider
        """
        # Update basic user information
        if "preferred_username" in claims:
            self.username = claims["preferred_username"]
        if "email" in claims:
            self.email = claims["email"]
        if "email_verified" in claims:
            self.is_verified = claims["email_verified"]
        if "given_name" in claims:
            self.first_name = claims["given_name"]
        if "family_name" in claims:
            self.last_name = claims["family_name"]

        # Update OIDC-specific fields
        if "sub" in claims:
            self.oidc_subject = claims["sub"]
        if "iss" in claims:
            self.oidc_issuer = claims["iss"]

        # Mark profile as completed if we have sufficient information
        if self.first_name and self.last_name and self.email:
            self.profile_completed = True

        self.save(
            update_fields=[
                "username",
                "email",
                "is_verified",
                "first_name",
                "last_name",
                "oidc_subject",
                "oidc_issuer",
                "profile_completed",
            ]
        )

    def is_oidc_user(self) -> bool:
        """
        Check if this user was authenticated via an OIDC provider.

        Returns:
            bool: True if the user has OIDC identifiers, False otherwise
        """
        return bool(self.oidc_subject and self.oidc_issuer)

    def get_oidc_claims(self) -> Dict[str, Union[str, bool, None]]:
        """
        Return standard OIDC claims for this user.
        Useful for integrating with django-allauth and external IDPs.
        """
        return {
            "sub": self.oidc_subject or str(self.id),
            "iss": self.oidc_issuer or None,
            "preferred_username": self.username,
            "email": self.email,
            "email_verified": self.is_verified,
            "name": self.get_full_name_oidc(),
            "given_name": self.first_name,
            "family_name": self.last_name,
        }

    def get_email_addresses(self) -> List[Dict[str, Union[str, bool]]]:
        """
        Return a list of email addresses associated with this user.
        This method is used by django-allauth to retrieve user emails.

        Returns:
            list: List of dictionaries with email address information
        """
        return [
            {
                "email": self.email,
                "verified": self.is_verified,
                "primary": True,  # Since we're using email as USERNAME_FIELD
            }
        ]

    def get_primary_email(self) -> str:
        """
        Return the primary email address for this user.
        This method is used by django-allauth for email operations.

        Returns:
            str: The primary email address
        """
        return self.email


class UserProfile(BaseModel):
    """
    Extended user profile with GDPR and privacy considerations.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", db_index=True
    )
    avatar = models.ImageField(
        upload_to=user_directory_path,
        blank=True,
        null=True,
        help_text=_(
            "User profile picture. Files are stored in MEDIA_ROOT/users/user_<id>/ directory. Depending on configuration, this may be local storage or cloud storage (e.g., AWS S3)."
        ),
    )
    avatar_thumbnail = ImageSpecField(
        source="avatar",
        processors=[ResizeToFill(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )

    # Additional profile fields with privacy considerations
    bio = models.TextField(
        _("bio"),
        blank=True,
        max_length=500,
        help_text=_("Brief description of yourself (max 500 characters)."),
        validators=[MaxLengthValidator(500)],
    )
    birth_date = models.DateField(
        _("birth date"),
        null=True,
        blank=True,
        help_text=_("Your birth date (optional)."),
        validators=[],
    )

    # Encrypted fields for sensitive data
    _encrypted_phone_number = models.TextField(
        _("encrypted phone number"),
        blank=True,
        help_text=_("Encrypted phone number for privacy protection."),
        validators=[
            RegexValidator(
                regex=r"^\+?[1-9]\d{1,14}$",
                message=_(
                    "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
                ),
            )
        ],
    )

    location = models.CharField(
        _("location"),
        max_length=100,
        blank=True,
        help_text=_("Your location (city, country, etc.)"),
        validators=[MaxLengthValidator(100)],
    )

    # Privacy settings
    show_email = models.BooleanField(
        _("show email"),
        default=False,
        help_text=_("Whether to display your email publicly."),
    )
    show_profile = models.BooleanField(
        _("show profile"),
        default=True,
        help_text=_("Whether your profile is visible to other users."),
    )

    # GDPR-related fields
    data_processing_consent = models.BooleanField(
        _("data processing consent"),
        default=False,
        help_text=_("Consent to process personal data for profile features."),
    )
    marketing_consent = models.BooleanField(
        _("marketing consent"),
        default=False,
        help_text=_("Consent to receive marketing communications."),
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        indexes = [
            models.Index(fields=["show_profile"]),
            models.Index(fields=["location"]),
            models.Index(fields=["data_processing_consent"]),
            models.Index(fields=["marketing_consent"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["bio"]),
        ]

    def clean(self):
        """
        Custom validation for the UserProfile model.
        """
        from django.core.exceptions import ValidationError

        # Validate that bio is not too long
        if self.bio and len(self.bio) > 500:
            raise ValidationError(_("Bio must be 500 characters or fewer."))

        # Validate that location is not too long
        if self.location and len(self.location) > 100:
            raise ValidationError(_("Location must be 100 characters or fewer."))

        super().clean()

    def save(self, *args, **kwargs):
        # Strip whitespace from text fields
        if self.bio:
            self.bio = self.bio.strip()
        if self.location:
            self.location = self.location.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

    @property
    def phone_number(self) -> str:
        """
        Get the decrypted phone number.

        Returns:
            str: The decrypted phone number or empty string if not set
        """
        if self._encrypted_phone_number:
            return decrypt_sensitive_data(self._encrypted_phone_number)
        return ""

    @phone_number.setter
    def phone_number(self, value: str | None) -> None:
        """
        Set and encrypt the phone number.

        Args:
            value (str): The phone number to set and encrypt
        """
        if value:
            self._encrypted_phone_number = encrypt_sensitive_data(value)
        else:
            self._encrypted_phone_number = ""

    def get_public_data(self) -> Dict[str, str]:
        """
        Return a dictionary of profile data that can be publicly shared,
        respecting privacy settings.
        """
        # Create a cache key based on the profile's state
        cache_key = f"user_profile_public_data_{self.id}_{self.updated_at.timestamp() if self.updated_at else 0}"

        # Try to get cached data
        from django.core.cache import cache

        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        public_data = {
            "username": self.user.username,
            "name": self.user.get_full_name_oidc(),
        }

        if self.show_profile:
            public_data.update(
                {
                    "bio": self.bio,
                    "location": self.location,
                }
            )

            if self.show_email:
                public_data["email"] = self.user.email

        # Cache the data for 5 minutes (30 seconds)
        cache.set(cache_key, public_data, 300)

        return public_data

    def update_privacy_settings(
        self,
        show_email: bool | None = None,
        show_profile: bool | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Update privacy settings for the user profile with audit logging.

        Args:
            show_email (bool, optional): Whether to display email publicly
            show_profile (bool, optional): Whether profile is visible to others
            ip_address (str, optional): IP address of the request
            user_agent (str, optional): User agent of the request
        """
        updated_fields = []
        original_settings = {}

        if show_email is not None:
            original_settings["show_email"] = self.show_email
            self.show_email = show_email
            updated_fields.append("show_email")

        if show_profile is not None:
            original_settings["show_profile"] = self.show_profile
            self.show_profile = show_profile
            updated_fields.append("show_profile")

        if updated_fields:
            self.save(update_fields=updated_fields)

            # Create audit log entry
            UserAuditLog.objects.create(
                user=self.user,
                action="profile_update",
                details={
                    "original_settings": original_settings,
                    "updated_settings": {
                        "show_email": self.show_email
                        if "show_email" in updated_fields
                        else original_settings.get("show_email"),
                        "show_profile": self.show_profile
                        if "show_profile" in updated_fields
                        else original_settings.get("show_profile"),
                    },
                    "updated_at": timezone.now().isoformat(),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

    def get_consent_summary(self) -> Dict[str, Union[bool, str, None]]:
        """
        Return a summary of user consents for privacy dashboard.

        Returns:
            dict: Dictionary with consent status for different purposes
        """
        # Create a cache key based on the profile's state
        cache_key = f"user_consent_summary_{self.id}_{self.updated_at.timestamp() if self.updated_at else 0}"

        # Try to get cached data
        from django.core.cache import cache

        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        consent_summary = {
            "data_processing": self.data_processing_consent,
            "marketing": self.marketing_consent,
            "last_updated": self.updated_at.isoformat()
            if hasattr(self, "updated_at")
            else None,
        }

        # Cache the data for 5 minutes (30 seconds)
        cache.set(cache_key, consent_summary, 300)

        return consent_summary

    def update_consents(
        self,
        data_processing: bool | None = None,
        marketing: bool | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Update user consent preferences with rate limiting and audit logging.

        Args:
            data_processing (bool, optional): Consent for data processing
            marketing (bool, optional): Consent for marketing communications
            ip_address (str, optional): IP address of the request
            user_agent (str, optional): User agent of the request
        """
        # Rate limiting: Check if user has updated consents too frequently
        from django.core.cache import cache
        from django.utils import timezone
        import logging

        logger = logging.getLogger(__name__)
        cache_key = f"consent_update_limit_{self.user.id}"
        last_update = cache.get(cache_key)

        if last_update:
            # Check if less than 1 minute has passed since last update
            time_since_last = timezone.now() - last_update
            if time_since_last.total_seconds() < 60:
                logger.warning(
                    f"Consent update rate limit exceeded for user {self.user.id}"
                )
                raise ValueError("Consent updates are rate limited to once per minute")

        updated_fields = []
        original_consents = {
            "data_processing": self.data_processing_consent,
            "marketing": self.marketing_consent,
        }

        if data_processing is not None:
            self.data_processing_consent = data_processing
            updated_fields.append("data_processing_consent")

            # If revoking data processing consent, also revoke marketing consent
            if not data_processing and self.marketing_consent:
                self.marketing_consent = False
                updated_fields.append("marketing_consent")

        if marketing is not None:
            # Can only give marketing consent if data processing consent is given
            if marketing and not self.data_processing_consent:
                raise ValueError(
                    "Data processing consent required for marketing consent"
                )
            self.marketing_consent = marketing
            updated_fields.append("marketing_consent")

        if updated_fields:
            self.save(update_fields=updated_fields)

            # Update rate limiting cache
            cache.set(cache_key, timezone.now(), timeout=60)

            # Create audit log entry
            UserAuditLog.objects.create(
                user=self.user,
                action="consent_update",
                details={
                    "original_consents": original_consents,
                    "updated_consents": {
                        "data_processing": self.data_processing_consent,
                        "marketing": self.marketing_consent,
                    },
                    "updated_at": timezone.now().isoformat(),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Consent updated for user {self.user.id}: {updated_fields}")
