"""
Tests for ``src/archive.py`` — folder compression and archive extraction.
"""

import io
import tarfile
from pathlib import Path

import pytest

from archive import compress_folder, extract_archive


# ---------------------------------------------------------------------------
# compress_folder
# ---------------------------------------------------------------------------


class TestCompressFolder:
    """Tests for in-memory tar.gz compression."""

    def test_returns_bytes_and_folder_name(self, sample_folder: Path):
        plaintext, name = compress_folder(sample_folder)
        assert isinstance(plaintext, bytes)
        assert name == "sample_folder"

    def test_plaintext_has_metadata_header(self, sample_folder: Path):
        """First 4 bytes are a little-endian length, followed by JSON metadata."""
        import json
        import struct

        plaintext, _ = compress_folder(sample_folder)
        meta_len = struct.unpack("<I", plaintext[:4])[0]
        meta = json.loads(plaintext[4 : 4 + meta_len])
        assert "folder_name" in meta
        assert meta["folder_name"] == "sample_folder"

    def test_archive_bytes_are_valid_gzip_tar(self, sample_folder: Path):
        import struct

        plaintext, _ = compress_folder(sample_folder)
        meta_len = struct.unpack("<I", plaintext[:4])[0]
        archive_bytes = plaintext[4 + meta_len :]

        buf = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            names = tar.getnames()
        # The top-level entry should be the folder name
        assert any("sample_folder" in n for n in names)

    def test_archive_contains_all_files(self, sample_folder: Path):
        import struct

        plaintext, _ = compress_folder(sample_folder)
        meta_len = struct.unpack("<I", plaintext[:4])[0]
        archive_bytes = plaintext[4 + meta_len :]

        buf = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            names = tar.getnames()

        # Expect: sample_folder, sample_folder/hello.txt,
        #         sample_folder/data.bin, sample_folder/subdir,
        #         sample_folder/subdir/nested.txt
        assert any(n.endswith("hello.txt") for n in names)
        assert any(n.endswith("data.bin") for n in names)
        assert any(n.endswith("nested.txt") for n in names)


# ---------------------------------------------------------------------------
# extract_archive
# ---------------------------------------------------------------------------


class TestExtractArchive:
    """Tests for safe tar.gz extraction."""

    def _make_archive(self, source_dir: Path) -> bytes:
        """Helper: create a valid tar.gz from a directory."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
        return buf.getvalue()

    def test_extracts_files(self, sample_folder: Path, tmp_path: Path):
        archive = self._make_archive(sample_folder)
        output = tmp_path / "output"
        output.mkdir()

        extract_archive(archive, output)

        assert (output / "sample_folder" / "hello.txt").read_text() == "Hello, world!"
        assert (output / "sample_folder" / "data.bin").read_bytes() == bytes(range(256))
        assert (output / "sample_folder" / "subdir" / "nested.txt").read_text() == "I am nested."

    def test_path_traversal_blocked(self, tmp_path: Path):
        """An archive with '../' in member names must be rejected."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="../escape.txt")
            info.size = 5
            tar.addfile(info, io.BytesIO(b"gotcha"))
        bad_archive = buf.getvalue()

        output = tmp_path / "output"
        output.mkdir()

        with pytest.raises(ValueError, match="escape"):
            extract_archive(bad_archive, output)

    def test_absolute_path_member_blocked(self, tmp_path: Path):
        """An archive with an absolute path member must be rejected."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = 4
            tar.addfile(info, io.BytesIO(b"root"))
        bad_archive = buf.getvalue()

        output = tmp_path / "output"
        output.mkdir()

        with pytest.raises(ValueError, match="escape"):
            extract_archive(bad_archive, output)
