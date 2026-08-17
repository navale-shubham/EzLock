"""
Tests for ``src/crypto.py`` — key derivation, encryption, and decryption.
"""

import json
import struct

import pytest

from constants import HEADER_MAGIC, KEY_SIZE, NONCE_SIZE, SALT_SIZE
from crypto import decrypt_payload, derive_key, encrypt_payload


# ---------------------------------------------------------------------------
# derive_key
# ---------------------------------------------------------------------------


class TestDeriveKey:
    """Unit tests for PBKDF2-HMAC-SHA256 key derivation."""

    def test_returns_correct_length(self):
        key = derive_key("password", b"\x00" * SALT_SIZE)
        assert len(key) == KEY_SIZE

    def test_deterministic(self):
        """Same inputs must always produce the same key."""
        salt = b"\xab" * SALT_SIZE
        k1 = derive_key("my-secret", salt)
        k2 = derive_key("my-secret", salt)
        assert k1 == k2

    def test_different_passwords_yield_different_keys(self):
        salt = b"\x01" * SALT_SIZE
        k1 = derive_key("password-a", salt)
        k2 = derive_key("password-b", salt)
        assert k1 != k2

    def test_different_salts_yield_different_keys(self):
        k1 = derive_key("password", b"\x00" * SALT_SIZE)
        k2 = derive_key("password", b"\xff" * SALT_SIZE)
        assert k1 != k2

    def test_unicode_password(self):
        """Non-ASCII passwords should work without error."""
        key = derive_key("pässwörd-日本語", b"\x00" * SALT_SIZE)
        assert len(key) == KEY_SIZE


# ---------------------------------------------------------------------------
# encrypt_payload / decrypt_payload  round-trip
# ---------------------------------------------------------------------------


def _make_plaintext(folder_name: str = "test_folder", body: bytes = b"ARCHIVE") -> bytes:
    """Build a plaintext blob with the metadata-header format that decrypt expects."""
    metadata = json.dumps({"folder_name": folder_name}).encode("utf-8")
    return struct.pack("<I", len(metadata)) + metadata + body


class TestEncryptDecryptRoundTrip:
    """Verify encrypt → decrypt yields the original data."""

    def test_basic_round_trip(self):
        plaintext = _make_plaintext("docs", b"compressed-tar-bytes")
        password = "hunter2"

        ez_blob = encrypt_payload(plaintext, password)
        archive, name = decrypt_payload(ez_blob, password)

        assert name == "docs"
        assert archive == b"compressed-tar-bytes"

    def test_empty_body_round_trip(self):
        plaintext = _make_plaintext("empty", b"")
        ez_blob = encrypt_payload(plaintext, "pw")
        archive, name = decrypt_payload(ez_blob, "pw")
        assert name == "empty"
        assert archive == b""

    def test_large_payload_round_trip(self):
        body = bytes(range(256)) * 1000  # ~256 KB
        plaintext = _make_plaintext("big", body)
        ez_blob = encrypt_payload(plaintext, "pass")
        archive, name = decrypt_payload(ez_blob, "pass")
        assert name == "big"
        assert archive == body


# ---------------------------------------------------------------------------
# encrypt_payload output format
# ---------------------------------------------------------------------------


class TestEncryptPayloadFormat:
    """Verify the binary layout of the .ez blob."""

    def test_starts_with_magic(self):
        ez = encrypt_payload(_make_plaintext(), "pw")
        assert ez[:8] == HEADER_MAGIC

    def test_contains_salt_nonce_ciphertext(self):
        ez = encrypt_payload(_make_plaintext(), "pw")
        # After magic we must have at least salt + nonce + some ciphertext
        header_len = len(HEADER_MAGIC) + SALT_SIZE + NONCE_SIZE
        assert len(ez) > header_len

    def test_each_encryption_produces_unique_output(self):
        """Random salt + nonce → different ciphertext each time."""
        plaintext = _make_plaintext()
        a = encrypt_payload(plaintext, "pw")
        b = encrypt_payload(plaintext, "pw")
        assert a != b


# ---------------------------------------------------------------------------
# decrypt_payload error handling
# ---------------------------------------------------------------------------


class TestDecryptErrors:
    """Edge cases and error paths for decryption."""

    def test_bad_magic_raises_value_error(self):
        with pytest.raises(ValueError, match="bad magic"):
            decrypt_payload(b"NOT_EZLK" + b"\x00" * 200, "pw")

    def test_wrong_password_raises_value_error(self):
        ez = encrypt_payload(_make_plaintext(), "right")
        with pytest.raises(ValueError, match="Wrong password|Decryption failed"):
            decrypt_payload(ez, "wrong")

    def test_truncated_blob_raises(self):
        ez = encrypt_payload(_make_plaintext(), "pw")
        # Chop off last 10 bytes → GCM tag is incomplete
        with pytest.raises((ValueError, Exception)):
            decrypt_payload(ez[:-10], "pw")

    def test_corrupted_ciphertext_raises(self):
        ez = bytearray(encrypt_payload(_make_plaintext(), "pw"))
        # Flip a byte in the ciphertext region
        ez[-1] ^= 0xFF
        with pytest.raises((ValueError, Exception)):
            decrypt_payload(bytes(ez), "pw")
