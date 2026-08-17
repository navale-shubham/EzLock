import os
import shutil
from pathlib import Path

from archive import compress_folder, extract_archive
from constants import EZ_EXTENSION
from crypto import decrypt_payload, encrypt_payload


def encrypt_folder(folder_path: Path, password: str) -> Path:
    """
    Compress and encrypt *folder_path*, then delete the original.

    Args:
        folder_path (Path): Path to the folder that should be encrypted.
        password (str): Encryption password supplied by the caller.

    Returns (Path):
        The path of the newly created .ez file.

    Raises:
        FileNotFoundError: If *folder_path* does not exist.
        NotADirectoryError: If *folder_path* is not a directory.
        FileExistsError: If the output .ez file already exists.
    """
    folder_path = folder_path.resolve()

    # Validation
    if not folder_path.exists():
        raise FileNotFoundError(f"'{folder_path}' does not exist.")
    if not folder_path.is_dir():
        raise NotADirectoryError(f"'{folder_path}' is not a folder.")

    output_path = folder_path.with_suffix(EZ_EXTENSION)
    if output_path.exists():
        raise FileExistsError(f"Output file '{output_path}' already exists.")

    # Compress → Encrypt
    print(f"Encrypting '{folder_path}' …")
    print(f"  Compressing '{folder_path.name}' …")
    plaintext, _ = compress_folder(folder_path)

    print("  Deriving key (this may take a moment) …")
    ez_bytes = encrypt_payload(plaintext, password)

    # Write output
    print(f"  Writing '{output_path}' …")
    with open(output_path, "wb") as fh:
        fh.write(ez_bytes)

    # Remove original
    print("  Removing original folder …")
    shutil.rmtree(folder_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"✓ Done. Encrypted file: '{output_path}' ({size_kb:.1f} KB)")

    return output_path


def decrypt_folder(ez_path: Path, password: str) -> Path:
    """
    Decrypt *ez_path* and extract the original folder, then delete the .ez file.

    Args:
        ez_path (Path): Path to the .ez file that should be decrypted.
        password (str): Decryption password supplied by the caller.

    Returns (Path):
        The path of the restored folder.

    Raises:
        FileNotFoundError: If *ez_path* does not exist.
        IsADirectoryError: If *ez_path* is a directory, not a file.
        FileExistsError: If the output folder already exists.
        ValueError: If the password is wrong or the file is corrupted.
    """
    ez_path = ez_path.resolve()

    # Validation
    if not ez_path.exists():
        raise FileNotFoundError(f"'{ez_path}' does not exist.")
    if not ez_path.is_file():
        raise IsADirectoryError(f"'{ez_path}' is not a file.")
    if not ez_path.suffix == EZ_EXTENSION:
        print(f"Warning: file does not have '{EZ_EXTENSION}' extension. Proceeding …")

    # Decrypt
    print(f"Decrypting '{ez_path}' …")
    print("  Deriving key (this may take a moment) …")

    with open(ez_path, "rb") as fh:
        ez_bytes = fh.read()

    archive_bytes, folder_name = decrypt_payload(ez_bytes, password)

    output_dir    = ez_path.parent
    output_folder = output_dir / folder_name

    if output_folder.exists():
        raise FileExistsError(f"Output folder '{output_folder}' already exists.")

    # Extract
    print(f"  Extracting to '{output_folder}' …")
    extract_archive(archive_bytes, output_dir)

    # Remove .ez file
    print("  Removing encrypted file …")
    os.remove(ez_path)

    size_kb = output_folder.stat().st_size / 1024
    print(f"✓ Done. Restored folder: '{output_folder}' ({size_kb:.1f} KB)")

    return output_folder
