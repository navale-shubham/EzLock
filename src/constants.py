"""
Shared configuration values for the ezlock file format and cryptographic
parameters.
"""

# Extension applied to every encrypted output file (e.g. Documents → Documents.ez)
EZ_EXTENSION: str = ".ez"

# 8-byte magic prefix that identifies a valid .ez file and encodes the format
# version. Bump the last two digits if the binary layout ever changes.
#
# Binary layout of a .ez file:
#   ┌─────────────┬────────────┬────────────┬──────────────────────────────┐
#   │  magic (8)  │  salt (32) │ nonce (12) │  ciphertext + GCM tag (var)  │
#   └─────────────┴────────────┴────────────┴──────────────────────────────┘
HEADER_MAGIC: bytes = b"EZLOCK01"


# Cryptographic parameters

# PBKDF2-HMAC-SHA256 iteration count.
# NIST SP 800-132 (2023) recommends a minimum of 600 000 for SHA-256.
PBKDF2_ITERATIONS: int = 600_000

# Random salt prepended to the file (protects against rainbow-table attacks).
SALT_SIZE: int = 32   # bytes → 256-bit salt

# AES key length. 32 bytes = AES-256.
KEY_SIZE: int = 32    # bytes

# GCM nonce (initialisation vector) length. 12 bytes is the GCM standard.
NONCE_SIZE: int = 12  # bytes
