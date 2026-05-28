"""
Helpers for compressing a folder into an in-memory tar.gz archive and for
safely extracting one back to disk.
"""

import io
import json
import os
import struct
import tarfile


# ── Compression ─────────────────────────────────────────────────────────────────

def compress_folder(folder_path: str) -> tuple[bytes, str]:
    """
    Compress *folder_path* into an in-memory tar.gz archive.

    The unencrypted archive is never written to disk; it lives entirely in a
    BytesIO buffer so the plaintext has minimal exposure.

    Plaintext layout written by this function (consumed by crypto.encrypt_payload):
        4-byte little-endian length of metadata JSON
        + metadata JSON  {"folder_name": "<name>"}
        + raw tar.gz bytes

    Args:
        folder_path: Absolute or relative path to the folder to compress.

    Returns:
        A tuple of (plaintext_bytes, folder_name).
    """
    folder_path = os.path.abspath(folder_path)
    folder_name = os.path.basename(folder_path)

    # Stream all files into an in-memory gzip-compressed tar archive
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(folder_path, arcname=folder_name)
    archive_bytes = buf.getvalue()

    # Prepend a small JSON metadata header so the original name survives
    # even if the .ez file is renamed before decryption.
    metadata  = json.dumps({"folder_name": folder_name}).encode("utf-8")
    meta_len  = struct.pack("<I", len(metadata))   # 4-byte little-endian length

    plaintext = meta_len + metadata + archive_bytes
    return plaintext, folder_name


# ── Extraction ──────────────────────────────────────────────────────────────────

def extract_archive(archive_bytes: bytes, output_dir: str) -> None:
    """
    Extract a tar.gz archive from *archive_bytes* into *output_dir*.

    Security: every member path is resolved with os.path.realpath and checked
    against *output_dir* to block path-traversal attacks (e.g. members that
    contain ``../`` or absolute paths).

    Args:
        archive_bytes: Raw tar.gz bytes (e.g. returned by :func:`compress_folder`).
        output_dir:    Directory into which files will be extracted.

    Raises:
        ValueError: If any archive member would escape *output_dir*.
    """
    real_output = os.path.realpath(output_dir)
    buf = io.BytesIO(archive_bytes)

    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        # Validate every member before extracting anything
        for member in tar.getmembers():
            member_path = os.path.realpath(os.path.join(output_dir, member.name))
            if not member_path.startswith(real_output):
                raise ValueError(
                    f"Archive member '{member.name}' would escape the output "
                    "directory. Aborting extraction."
                )

        tar.extractall(path=output_dir)
