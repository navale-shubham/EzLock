"""
High-level workflow functions that orchestrate the individual modules:

  encrypt_folder  →  validate → compress → encrypt → write → delete original
  decrypt_folder  →  validate → read → decrypt → extract → delete .ez file
"""

import os
import shutil

import click

from .archive import compress_folder, extract_archive
from .constants import EZ_EXTENSION
from .crypto import decrypt_payload, encrypt_payload


# ── Encrypt ─────────────────────────────────────────────────────────────────────

def encrypt_folder(folder_path: str, password: str) -> str:
    """
    Compress and encrypt *folder_path*, then delete the original.

    Args:
        folder_path: Path to the folder that should be encrypted.
        password:    Encryption password supplied by the caller.

    Returns:
        The path of the newly created .ez file.

    Raises:
        FileNotFoundError: If *folder_path* does not exist.
        NotADirectoryError: If *folder_path* is not a directory.
        FileExistsError: If the output .ez file already exists.
    """
    folder_path = os.path.abspath(folder_path)

    # ── Validation ───────────────────────────────────────────────────────────
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"'{folder_path}' does not exist.")
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"'{folder_path}' is not a folder.")

    output_path = folder_path + EZ_EXTENSION
    if os.path.exists(output_path):
        raise FileExistsError(f"Output file '{output_path}' already exists.")

    # ── Compress → Encrypt ───────────────────────────────────────────────────
    click.echo(f"\n[ezlock] Encrypting '{folder_path}' …")

    click.echo(f"  Compressing '{os.path.basename(folder_path)}' …")
    plaintext, _ = compress_folder(folder_path)

    click.echo("  Deriving key (this may take a moment) …")
    ez_bytes = encrypt_payload(plaintext, password)

    # ── Write output ─────────────────────────────────────────────────────────
    click.echo(f"  Writing '{output_path}' …")
    with open(output_path, "wb") as fh:
        fh.write(ez_bytes)

    # ── Remove original ──────────────────────────────────────────────────────
    click.echo("  Removing original folder …")
    shutil.rmtree(folder_path)

    size_kb = os.path.getsize(output_path) / 1024
    click.secho(f"\n✓ Done. Encrypted file: '{output_path}' ({size_kb:.1f} KB)", fg="green")

    return output_path


# ── Decrypt ─────────────────────────────────────────────────────────────────────

def decrypt_folder(ez_path: str, password: str) -> str:
    """
    Decrypt *ez_path* and extract the original folder, then delete the .ez file.

    Args:
        ez_path:  Path to the .ez file that should be decrypted.
        password: Decryption password supplied by the caller.

    Returns:
        The path of the restored folder.

    Raises:
        FileNotFoundError: If *ez_path* does not exist.
        IsADirectoryError: If *ez_path* is a directory, not a file.
        FileExistsError: If the output folder already exists.
        ValueError: If the password is wrong or the file is corrupted.
    """
    ez_path = os.path.abspath(ez_path)

    # ── Validation ───────────────────────────────────────────────────────────
    if not os.path.exists(ez_path):
        raise FileNotFoundError(f"'{ez_path}' does not exist.")
    if not os.path.isfile(ez_path):
        raise IsADirectoryError(f"'{ez_path}' is not a file.")
    if not ez_path.endswith(EZ_EXTENSION):
        click.echo(
            f"Warning: file does not have '{EZ_EXTENSION}' extension. Proceeding …",
            err=True,
        )

    # ── Decrypt ──────────────────────────────────────────────────────────────
    click.echo(f"\n[ezlock] Decrypting '{ez_path}' …")
    click.echo("  Deriving key (this may take a moment) …")

    with open(ez_path, "rb") as fh:
        ez_bytes = fh.read()

    archive_bytes, folder_name = decrypt_payload(ez_bytes, password)

    output_dir    = os.path.dirname(ez_path)
    output_folder = os.path.join(output_dir, folder_name)

    if os.path.exists(output_folder):
        raise FileExistsError(f"Output folder '{output_folder}' already exists.")

    # ── Extract ──────────────────────────────────────────────────────────────
    click.echo(f"  Extracting to '{output_folder}' …")
    extract_archive(archive_bytes, output_dir)

    # ── Remove .ez file ───────────────────────────────────────────────────────
    click.echo("  Removing encrypted file …")
    os.remove(ez_path)

    click.secho(f"\n✓ Done. Restored folder: '{output_folder}'", fg="green")

    return output_folder
