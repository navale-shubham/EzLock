"""
Tests for ``src/constants.py`` — verify that all cryptographic constants are
correctly defined and consistent with the documented .ez binary format.
"""

from constants import (
    EZ_EXTENSION,
    HEADER_MAGIC,
    KEY_SIZE,
    NONCE_SIZE,
    PBKDF2_ITERATIONS,
    SALT_SIZE,
)


class TestConstants:
    """Sanity checks on the shared constants."""

    def test_extension_starts_with_dot(self):
        assert EZ_EXTENSION.startswith(".")

    def test_header_magic_is_8_bytes(self):
        assert len(HEADER_MAGIC) == 8

    def test_header_magic_value(self):
        assert HEADER_MAGIC == b"EZLOCK01"

    def test_pbkdf2_iterations_minimum(self):
        """NIST SP 800-132 recommends ≥ 600 000 for SHA-256."""
        assert PBKDF2_ITERATIONS >= 600_000

    def test_salt_size_is_32(self):
        assert SALT_SIZE == 32

    def test_key_size_is_32(self):
        """AES-256 requires a 32-byte key."""
        assert KEY_SIZE == 32

    def test_nonce_size_is_12(self):
        """GCM standard nonce length is 12 bytes."""
        assert NONCE_SIZE == 12
