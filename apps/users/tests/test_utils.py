# apps/users/tests/test_utils.py
"""
Unit tests for user utility functions.

These tests verify the correctness and security of utility functions
used in user management, particularly encryption/decryption operations.
"""

import os
import sys
from unittest.mock import patch

# Use Django's test runner to properly configure settings
import django
from django.conf import settings
from django.test import TestCase, override_settings

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Configure Django settings if not already configured
if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    django.setup()

# Import our modules after Django is configured
from apps.users.utils import (  # noqa: E402
    get_encryption_key,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
)


class EncryptionUtilsTestCase(TestCase):
    """
    Test case for encryption utility functions.
    """

    def test_get_encryption_key_deterministic(self):
        """
        Test that get_encryption_key produces the same key for the same SECRET_KEY.
        """
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        self.assertEqual(key1, key2)

    @override_settings(SECRET_KEY="test-secret-key-1")
    def test_get_encryption_key_different_secrets(self):
        """
        Test that get_encryption_key produces different keys for different SECRET_KEYs.
        """
        key1 = get_encryption_key()

        with override_settings(SECRET_KEY="test-secret-key-2"):
            key2 = get_encryption_key()

        self.assertNotEqual(key1, key2)

    def test_encrypt_decrypt_roundtrip(self):
        """
        Test that encrypt/decrypt is a proper round-trip operation.
        """
        original_data = "This is a test message for encryption"
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertNotEqual(original_data, encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_encrypt_decrypt_empty_string(self):
        """
        Test that encrypt/decrypt handles empty strings correctly.
        """
        original_data = ""
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertEqual(original_data, encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_encrypt_decrypt_none_value(self):
        """
        Test that encrypt/decrypt handles None values gracefully.
        """
        encrypted_data = encrypt_sensitive_data(None)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertEqual("", encrypted_data)
        self.assertEqual("", decrypted_data)

    def test_encrypt_decrypt_special_characters(self):
        """
        Test that encrypt/decrypt handles special characters correctly.
        """
        original_data = "Test with spëcïal chäråctérs! @#$%^&*()"
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertNotEqual(original_data, encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_encrypt_decrypt_unicode(self):
        """
        Test that encrypt/decrypt handles Unicode characters correctly.
        """
        original_data = "测试中文数据 🚀🌟🎉"
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertNotEqual(original_data, encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_decrypt_invalid_data_returns_empty_string(self):
        """
        Test that decrypt returns empty string for invalid encrypted data.
        This prevents information disclosure from malformed data.
        """
        invalid_encrypted_data = "this-is-not-valid-encrypted-data"
        decrypted_data = decrypt_sensitive_data(invalid_encrypted_data)

        self.assertEqual("", decrypted_data)

    def test_encrypt_decrypt_large_data(self):
        """
        Test that encrypt/decrypt handles large data correctly.
        """
        original_data = "A" * 10000  # 10KB of data
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)

        self.assertNotEqual(original_data, encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_encrypt_same_data_different_output(self):
        """
        Test that encrypting the same data twice produces different outputs.
        This ensures semantic security through random IV generation.
        """
        original_data = "Same message encrypted twice"
        encrypted_data1 = encrypt_sensitive_data(original_data)
        encrypted_data2 = encrypt_sensitive_data(original_data)

        # The encrypted data should be different due to random IV
        self.assertNotEqual(encrypted_data1, encrypted_data2)

        # But both should decrypt to the same original data
        decrypted_data1 = decrypt_sensitive_data(encrypted_data1)
        decrypted_data2 = decrypt_sensitive_data(encrypted_data2)

        self.assertEqual(original_data, decrypted_data1)
        self.assertEqual(original_data, decrypted_data2)

    def test_encrypt_sensitive_data_error_handling(self):
        """
        Test error handling in encrypt_sensitive_data function.
        """
        # Test with invalid data type (should handle gracefully)
        with patch('apps.users.utils.get_encryption_key') as mock_key:
            # Mock an invalid key that will cause encryption to fail
            mock_key.return_value = b'invalid-key'
            
            # Should return empty string on encryption failure
            result = encrypt_sensitive_data("test data")
            self.assertEqual(result, "")

    def test_decrypt_sensitive_data_error_handling(self):
        """
        Test error handling in decrypt_sensitive_data function.
        """
        # Test with invalid encrypted data (should return empty string)
        result = decrypt_sensitive_data("invalid-encrypted-data")
        self.assertEqual(result, "")
        
        # Test with None input (should return empty string)
        result = decrypt_sensitive_data(None)
        self.assertEqual(result, "")
        
        # Test with empty string input (should return empty string)
        result = decrypt_sensitive_data("")
        self.assertEqual(result, "")

    def test_get_encryption_key_cache_behavior(self):
        """
        Test caching behavior of get_encryption_key function.
        """
        from django.core.cache import cache
        
        # Clear cache first
        cache.delete("user_encryption_key")
        
        # Get key for the first time
        key1 = get_encryption_key()
        
        # Get key for the second time (should be cached)
        key2 = get_encryption_key()
        
        # Keys should be identical
        self.assertEqual(key1, key2)

    def test_encrypt_decrypt_with_special_input(self):
        """
        Test encrypt/decrypt with special input cases.
        """
        # Test with very long data
        long_data = "A" * 100000  # 100KB of data
        encrypted = encrypt_sensitive_data(long_data)
        decrypted = decrypt_sensitive_data(encrypted)
        self.assertEqual(long_data, decrypted)
        
        # Test with data containing newlines and tabs
        multiline_data = "Line 1\nLine 2\tTabbed\tContent\nLine 3"
        encrypted = encrypt_sensitive_data(multiline_data)
        decrypted = decrypt_sensitive_data(encrypted)
        self.assertEqual(multiline_data, decrypted)


# Add a main block to allow running tests directly
if __name__ == "__main__":
    import unittest

    unittest.main()
