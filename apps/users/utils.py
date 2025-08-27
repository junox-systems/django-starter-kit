# apps/users/utils.py
"""
Utility functions for user management, including encryption and data handling.

This module provides secure utility functions for handling sensitive user data,
including encryption/decryption operations using industry-standard cryptography.
"""

import logging
import base64
import os
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """
    Get encryption key derived from Django's SECRET_KEY using HKDF for production use.

    This function derives a cryptographically secure 32-byte key from
    Django's SECRET_KEY using HKDF (HMAC-based Key Derivation Function).
    HKDF is specifically designed for key derivation and provides better
    security properties than simple hashing.

    Security Notes:
    - Uses deterministic derivation (salt=None) for consistent key generation
    - Includes application-specific info parameter for context separation
    - For key rotation scenarios, consider implementing salt-based versioning

    Returns:
        bytes: The encryption key suitable for Fernet (32 url-safe base64-encoded bytes)
    """

    # Check if we have a cached key
    cache_key = "user_encryption_key"
    cached_key = cache.get(cache_key)
    if cached_key:
        return cached_key

    # Derive a 32-byte key using HKDF with SHA-256
    # Using salt=None for deterministic derivation - same input always produces same key
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet requires exactly 32 bytes
        salt=None,  # Deterministic derivation; for key rotation, use unique salt per version
        info=b"user-profile-encryption",  # Application-specific context
    )
    key = hkdf.derive(settings.SECRET_KEY.encode())

    # Fernet requires a url-safe base64-encoded 32-byte key
    derived_key = base64.urlsafe_b64encode(key)

    # Cache the key for 1 hour (3600 seconds)
    cache.set(cache_key, derived_key, 3600)

    return derived_key


def encrypt_sensitive_data(data: Optional[str]) -> str:
    """
    Encrypt sensitive data using Fernet (AES 128-bit encryption with HMAC authentication).

    Fernet guarantees that a message encrypted using it cannot be manipulated
    or read without the key. It uses AES 128 in CBC mode and HMAC for authentication.

    Security Features:
    - Authenticated encryption (prevents tampering)
    - Random IV generation for semantic security
    - Constant-time HMAC verification
    - Automatic padding handling

    Args:
        data (str, optional): The plaintext data to encrypt

    Returns:
        str: The encrypted data as a base64-encoded string, or empty string if encryption fails
    """
    # Handle empty/null data case
    if not data:
        return ""
    try:
        # Get the 32-byte encryption key derived from Django's SECRET_KEY
        key = get_encryption_key()

        # Create Fernet instance with the key
        f = Fernet(key)

        # Encrypt the data (Fernet automatically handles:
        # - Generating a 128-bit random IV
        # - Padding the plaintext to block size
        # - Encrypting with AES-CBC
        # - Creating HMAC for authentication)
        encrypted_data = f.encrypt(data.encode())

        # Return as string (Fernet returns base64-encoded bytes)
        return encrypted_data.decode()
    except ValueError as e:
        # Handle value errors (e.g., invalid data encoding)
        if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.test":
            logger.error(
                f"Encryption failed due to invalid data: {str(e)}", exc_info=True
            )
        return ""
    except Exception as e:
        # Handle all other exceptions
        if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.test":
            logger.error(f"Encryption failed unexpectedly: {str(e)}", exc_info=True)
        return ""


def decrypt_sensitive_data(encrypted_data: Optional[str]) -> str:
    """
    Decrypt sensitive data using Fernet.

    Fernet verifies the HMAC signature before decryption to ensure
    the data has not been tampered with. If verification fails,
    an InvalidToken exception is raised.

    Security Notes:
    - Returns empty string on decryption failure to prevent information disclosure
    - All exceptions are logged but not exposed to prevent side-channel attacks

    Args:
        encrypted_data (str, optional): The base64-encoded encrypted data

    Returns:
        str: The decrypted plaintext data, or empty string if decryption fails
    """
    # Handle empty/null data case
    if not encrypted_data:
        return ""
    try:
        # Get the 32-byte encryption key derived from Django's SECRET_KEY
        key = get_encryption_key()

        # Create Fernet instance with the key
        f = Fernet(key)

        # Decrypt the data (Fernet automatically handles:
        # - Verifying the HMAC signature
        # - Decrypting with AES-CBC
        # - Removing padding)
        decrypted_data = f.decrypt(encrypted_data.encode())

        # Return as string
        return decrypted_data.decode()
    except ValueError as e:
        # Handle value errors (e.g., invalid data encoding)
        if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.test":
            logger.error(
                f"Decryption failed due to invalid data: {str(e)}", exc_info=True
            )
        # Return empty string to prevent information disclosure
        return ""
    except Exception as e:
        # Handle all other exceptions
        if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.test":
            logger.error(f"Decryption failed unexpectedly: {str(e)}", exc_info=True)
        # Return empty string to prevent information disclosure
        return ""
