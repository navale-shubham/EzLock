"""
Low-level cryptographic primitives:
  - PBKDF2-HMAC-SHA256 key derivation
  - AES-256-GCM authenticated encryption / decryption
"""

import hashlib
import secrets
import struct
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from constants import (
    HEADER_MAGIC,
    KEY_SIZE,
    NONCE_SIZE,
    PBKDF2_ITERATIONS,
    SALT_SIZE,
)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit AES key from *password* using PBKDF2-HMAC-SHA256.

    Args:
        password: The user-supplied plaintext password.
        salt:     A cryptographically random salt (SALT_SIZE bytes).

    Returns:
        A KEY_SIZE-byte derived key suitable for AES-256.
    """
    return hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        dklen=KEY_SIZE,
    )


def encrypt_payload(plaintext: bytes, password: str) -> bytes:
    """
    Encrypt *plaintext* with AES-256-GCM and return a self-contained .ez blob.

    The returned bytes embed everything needed for decryption (salt, nonce,
    ciphertext, and GCM authentication tag) after the HEADER_MAGIC prefix.

    Args:
        plaintext: Raw bytes to encrypt (metadata header + tar.gz archive).
        password:  User-supplied password used for key derivation.

    Returns:
        Full .ez file bytes: HEADER_MAGIC | salt | nonce | ciphertext+tag
    """
    salt  = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    key   = derive_key(password, salt)

    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)

    return HEADER_MAGIC + salt + nonce + ciphertext


def decrypt_payload(ez_bytes: bytes, password: str) -> tuple[bytes, str]:
    """
    Decrypt a .ez blob and return the embedded tar.gz archive plus folder name.

    Parses the binary layout produced by :func:`encrypt_payload`, re-derives
    the key, and authenticates + decrypts with AES-256-GCM.

    Args:
        ez_bytes: Raw bytes read from a .ez file.
        password: User-supplied password.

    Returns:
        A tuple of (archive_bytes, original_folder_name).

    Raises:
        ValueError: If the magic header is invalid, the password is wrong,
                    or the ciphertext has been tampered with.
    """
    # Validate magic
    if not ez_bytes.startswith(HEADER_MAGIC):
        raise ValueError("Not a valid .ez file (bad magic bytes).")

    # Parse header fields
    offset = len(HEADER_MAGIC)

    salt  = ez_bytes[offset : offset + SALT_SIZE];  offset += SALT_SIZE
    nonce = ez_bytes[offset : offset + NONCE_SIZE]; offset += NONCE_SIZE
    ciphertext = ez_bytes[offset:]

    # Authenticated decryption
    key = derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except Exception:
        # GCM tag mismatch → wrong password or corrupted bytes
        raise ValueError("Decryption failed. Wrong password or corrupted file.")

    # Parse embedded metadata
    # Plaintext layout: 4-byte LE metadata length | metadata JSON | tar.gz bytes
    meta_len     = struct.unpack("<I", plaintext[:4])[0]
    metadata     = json.loads(plaintext[4 : 4 + meta_len].decode("utf-8"))
    archive_bytes = plaintext[4 + meta_len:]

    return archive_bytes, metadata["folder_name"]
