"""
Shared pytest fixtures for the EzLock test suite.

Adds ``src/`` to sys.path so that the source modules are importable without
installing the package, and provides reusable temporary-folder helpers.
"""

import sys
from pathlib import Path

import pytest

# Make src/ importable
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture()
def sample_folder(tmp_path: Path) -> Path:
    """Create a small sample folder with a few files for testing."""
    folder = tmp_path / "sample_folder"
    folder.mkdir()

    (folder / "hello.txt").write_text("Hello, world!", encoding="utf-8")
    (folder / "data.bin").write_bytes(bytes(range(256)))

    sub = folder / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("I am nested.", encoding="utf-8")

    return folder


@pytest.fixture()
def password() -> str:
    """A deterministic password used across tests."""
    return "correct-horse-battery-staple"
