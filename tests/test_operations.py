"""
Tests for ``src/operations.py`` — high-level encrypt_folder / decrypt_folder
workflows.

These are integration-style tests: they exercise the full pipeline from
folder → .ez file → restored folder.
"""

from pathlib import Path

import pytest

from constants import EZ_EXTENSION
from operations import decrypt_folder, encrypt_folder


# ---------------------------------------------------------------------------
# encrypt_folder
# ---------------------------------------------------------------------------


class TestEncryptFolder:
    """Tests for the encrypt_folder workflow."""

    def test_creates_ez_file(self, sample_folder: Path, password: str):
        ez_path = encrypt_folder(sample_folder, password)
        assert ez_path.exists()
        assert ez_path.suffix == EZ_EXTENSION

    def test_removes_original_folder(self, sample_folder: Path, password: str):
        encrypt_folder(sample_folder, password)
        assert not sample_folder.exists()

    def test_file_not_found_raises(self, tmp_path: Path, password: str):
        with pytest.raises(FileNotFoundError):
            encrypt_folder(tmp_path / "nonexistent", password)

    def test_not_a_directory_raises(self, tmp_path: Path, password: str):
        f = tmp_path / "file.txt"
        f.write_text("I'm a file")
        with pytest.raises(NotADirectoryError):
            encrypt_folder(f, password)

    def test_output_already_exists_raises(self, sample_folder: Path, password: str):
        # Pre-create the .ez file
        ez_file = sample_folder.with_suffix(EZ_EXTENSION)
        ez_file.write_bytes(b"dummy")
        with pytest.raises(FileExistsError):
            encrypt_folder(sample_folder, password)


# ---------------------------------------------------------------------------
# decrypt_folder
# ---------------------------------------------------------------------------


class TestDecryptFolder:
    """Tests for the decrypt_folder workflow."""

    def test_restores_original_folder(self, sample_folder: Path, password: str):
        ez_path = encrypt_folder(sample_folder, password)
        restored = decrypt_folder(ez_path, password)

        assert restored.exists()
        assert restored.is_dir()
        assert (restored / "hello.txt").read_text() == "Hello, world!"
        assert (restored / "data.bin").read_bytes() == bytes(range(256))
        assert (restored / "subdir" / "nested.txt").read_text() == "I am nested."

    def test_removes_ez_file(self, sample_folder: Path, password: str):
        ez_path = encrypt_folder(sample_folder, password)
        decrypt_folder(ez_path, password)
        assert not ez_path.exists()

    def test_wrong_password_raises(self, sample_folder: Path, password: str):
        ez_path = encrypt_folder(sample_folder, password)
        with pytest.raises(ValueError, match="Wrong password|Decryption failed"):
            decrypt_folder(ez_path, "wrong-password")

    def test_file_not_found_raises(self, tmp_path: Path, password: str):
        with pytest.raises(FileNotFoundError):
            decrypt_folder(tmp_path / "missing.ez", password)

    def test_is_a_directory_raises(self, tmp_path: Path, password: str):
        d = tmp_path / "a_dir"
        d.mkdir()
        with pytest.raises(IsADirectoryError):
            decrypt_folder(d, password)

    def test_output_folder_exists_raises(self, sample_folder: Path, password: str):
        ez_path = encrypt_folder(sample_folder, password)
        # Re-create the folder to trigger the conflict
        sample_folder.mkdir()
        (sample_folder / "hello.txt").write_text("block")
        with pytest.raises(FileExistsError):
            decrypt_folder(ez_path, password)


# ---------------------------------------------------------------------------
# Full round-trip
# ---------------------------------------------------------------------------


class TestFullRoundTrip:
    """End-to-end: encrypt → decrypt → verify contents byte-for-byte."""

    def test_round_trip_preserves_all_content(self, sample_folder: Path, password: str):
        # Snapshot original contents
        original_files = {}
        for p in sorted(sample_folder.rglob("*")):
            if p.is_file():
                rel = p.relative_to(sample_folder)
                original_files[str(rel)] = p.read_bytes()

        ez_path = encrypt_folder(sample_folder, password)
        restored = decrypt_folder(ez_path, password)

        # Verify every file matches
        restored_files = {}
        for p in sorted(restored.rglob("*")):
            if p.is_file():
                rel = p.relative_to(restored)
                restored_files[str(rel)] = p.read_bytes()

        assert original_files == restored_files
