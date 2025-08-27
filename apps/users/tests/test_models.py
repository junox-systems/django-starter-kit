# apps/users/tests/test_models.py
"""
Unit tests for user models.

These tests verify the correctness of user model functionality,
including encryption, privacy settings, and consent management.
"""

import os
import sys

# Import Django test framework after setup
from django.test import TestCase
from django.contrib.auth import get_user_model
# from apps.users.models import UserProfile

# Use Django's test runner to properly configure settings
import django
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    django.setup()

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)


User = get_user_model()


class UserProfileTestCase(TestCase):
    """
    Test case for UserProfile model functionality.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        # The UserProfile is automatically created by signals, so we just get it
        self.profile = self.user.profile

    def test_phone_number_encryption_property(self):
        """
        Test that phone_number property encrypts on set and decrypts on get.
        """
        phone_number = "+1-555-123-4567"

        # Set phone number (should encrypt)
        self.profile.phone_number = phone_number
        self.profile.save()

        # Get phone number (should decrypt)
        retrieved_phone = self.profile.phone_number

        # Verify the values match
        self.assertEqual(phone_number, retrieved_phone)

        # Verify the stored value is encrypted (different from original)
        self.assertNotEqual(phone_number, self.profile._encrypted_phone_number)

    def test_phone_number_encryption_empty_values(self):
        """
        Test that phone_number property handles empty values correctly.
        """
        # Test setting empty string
        self.profile.phone_number = ""
        self.profile.save()
        self.assertEqual("", self.profile.phone_number)

        # Test setting None
        self.profile.phone_number = None
        self.profile.save()
        self.assertEqual("", self.profile.phone_number)

    def test_phone_number_encryption_special_characters(self):
        """
        Test that phone_number property handles special characters correctly.
        """
        phone_number = "+1 (555) 123-4567 ext. 999"

        # Set phone number with special characters
        self.profile.phone_number = phone_number
        self.profile.save()

        # Get and verify
        retrieved_phone = self.profile.phone_number
        self.assertEqual(phone_number, retrieved_phone)

    def test_phone_number_encryption_international(self):
        """
        Test that phone_number property handles international numbers correctly.
        """
        phone_number = "+44 20 7946 0958"  # UK number format

        # Set international phone number
        self.profile.phone_number = phone_number
        self.profile.save()

        # Get and verify
        retrieved_phone = self.profile.phone_number
        self.assertEqual(phone_number, retrieved_phone)

    def test_get_public_data_respects_privacy_settings(self):
        """
        Test that get_public_data respects privacy settings.
        """
        # Set up profile with data
        self.profile.bio = "Software developer"
        self.profile.location = "San Francisco, CA"
        self.profile.show_profile = True
        self.profile.show_email = True
        self.profile.save()

        # Get public data when profile is visible and email is shown
        public_data = self.profile.get_public_data()
        self.assertIn("bio", public_data)
        self.assertIn("location", public_data)
        self.assertIn("email", public_data)
        self.assertEqual(public_data["email"], self.user.email)

        # Hide profile
        self.profile.show_profile = False
        self.profile.save()

        # Get public data when profile is hidden
        public_data = self.profile.get_public_data()
        self.assertNotIn("bio", public_data)
        self.assertNotIn("location", public_data)
        self.assertNotIn("email", public_data)

        # Show profile but hide email
        self.profile.show_profile = True
        self.profile.show_email = False
        self.profile.save()

        # Get public data when profile is visible but email is hidden
        public_data = self.profile.get_public_data()
        self.assertIn("bio", public_data)
        self.assertIn("location", public_data)
        self.assertNotIn("email", public_data)

    def test_update_privacy_settings_edge_cases(self):
        """
        Test edge cases for update_privacy_settings method.
        """
        # Test updating with None values (should not change anything)
        original_show_email = self.profile.show_email
        original_show_profile = self.profile.show_profile
        
        self.profile.update_privacy_settings(show_email=None, show_profile=None)
        
        # Values should remain unchanged
        self.assertEqual(self.profile.show_email, original_show_email)
        self.assertEqual(self.profile.show_profile, original_show_profile)
        
        # Test updating only one setting
        self.profile.update_privacy_settings(show_email=True)
        self.assertTrue(self.profile.show_email)
        self.assertEqual(self.profile.show_profile, original_show_profile)  # Should be unchanged
        
        self.profile.update_privacy_settings(show_profile=False)
        self.assertFalse(self.profile.show_profile)
        self.assertTrue(self.profile.show_email)  # Should be unchanged

    def test_get_consent_summary_edge_cases(self):
        """
        Test edge cases for get_consent_summary method.
        """
        # Test with no updated_at field
        summary = self.profile.get_consent_summary()
        self.assertIn("data_processing", summary)
        self.assertIn("marketing", summary)
        # last_updated might be None if updated_at doesn't exist
        
    def test_update_consents_edge_cases(self):
        """
        Test edge cases for update_consents method.
        """
        # Test updating with None values (should not change anything)
        original_data_processing = self.profile.data_processing_consent
        original_marketing = self.profile.marketing_consent
        
        self.profile.update_consents(data_processing=None, marketing=None)
        
        # Values should remain unchanged
        self.assertEqual(self.profile.data_processing_consent, original_data_processing)
        self.assertEqual(self.profile.marketing_consent, original_marketing)
        
        # Test giving marketing consent without data processing consent
        with self.assertRaises(ValueError) as context:
            self.profile.update_consents(marketing=True)
        self.assertIn("Data processing consent required", str(context.exception))
        
        # Test revoking data processing consent also revokes marketing consent
        self.profile.data_processing_consent = True
        self.profile.marketing_consent = True
        self.profile.save()
        
        self.profile.update_consents(data_processing=False)
        self.assertFalse(self.profile.data_processing_consent)
        self.assertFalse(self.profile.marketing_consent)

    def test_user_model_methods_edge_cases(self):
        """
        Test edge cases for User model methods.
        """
        # Test get_full_name_oidc with empty name
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        
        full_name = self.user.get_full_name_oidc()
        self.assertEqual(full_name, self.user.username)
        
        # Test is_oidc_user with None values
        self.user.oidc_subject = None
        self.user.oidc_issuer = None
        self.user.save()
        
        self.assertFalse(self.user.is_oidc_user())
        
        # Test get_oidc_claims with None oidc_subject
        claims = self.user.get_oidc_claims()
        self.assertEqual(claims["sub"], str(self.user.id))
        self.assertIsNone(claims["iss"])

    def test_user_audit_log_str_representation(self):
        """
        Test the string representation of UserAuditLog.
        """
        # Create an audit log entry
        from apps.users.models import UserAuditLog
        audit_log = UserAuditLog.objects.create(
            user=self.user,
            action="profile_update",
            details={"test": "data"}
        )
        
        # Test string representation
        str_repr = str(audit_log)
        self.assertIn(self.user.email, str_repr)
        self.assertIn("profile_update", str_repr)


# Add a main block to allow running tests directly
if __name__ == "__main__":
    import unittest

    unittest.main()
