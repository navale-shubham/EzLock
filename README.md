# ezlock — Folder Encryption CLI

Encrypt and decrypt entire folders with a single command.  
Uses **AES-256-GCM** (authenticated encryption) with a **PBKDF2-derived key**.

---

## Project Structure

```
EzLock/
├── pyproject.toml            # Package metadata (v2.0.0)
├── README.md
├── uv.lock
├── src/
│   ├── main.py               # Typer CLI entry point
│   ├── operations.py          # High-level encrypt / decrypt workflows
│   ├── crypto.py              # AES-256-GCM + PBKDF2 key derivation
│   ├── archive.py             # tar.gz compress / safe-extract
│   └── constants.py           # Shared magic values & crypto parameters
└── tests/
    ├── conftest.py            # Shared fixtures (tmp folders, passwords, …)
    ├── test_archive.py        # Compression & extraction tests
    ├── test_constants.py      # Constant-value sanity checks
    ├── test_crypto.py         # Encrypt / decrypt / KDF tests
    └── test_operations.py     # End-to-end workflow tests
```

---

## Quick Start

```bash
# Install dependencies
uv sync

# Encrypt a folder (will prompt for password)
uv run python src/main.py encrypt Documents/

# Decrypt a .ez file (will prompt for password)
uv run python src/main.py decrypt Documents.ez
```

---

## CLI Reference

```
python src/main.py encrypt FOLDER
python src/main.py decrypt FILE
```

Both commands prompt interactively for a password (input is masked with `*`).  
The `encrypt` command asks you to confirm the password a second time.

**Examples:**
```bash
# Encrypt ~/Documents → ~/Documents.ez
uv run python src/main.py encrypt ~/Documents

# Decrypt ~/Documents.ez → ~/Documents
uv run python src/main.py decrypt ~/Documents.ez
```

---

## Running Tests

All tests use **pytest** and live in the `tests/` directory.

```bash
# Run the full suite
uv run pytest

# Verbose output
uv run pytest ./tests -v
```

---

## How It Works

### Encryption
1. Folder → in-memory **tar.gz** (never touches disk unencrypted).
2. Metadata header `{"folder_name": "…"}` prepended so the original name survives renaming.
3. Random **32-byte salt** + **12-byte nonce** generated via `secrets`.
4. **256-bit AES key** derived from password via **PBKDF2-HMAC-SHA256** (600 000 iterations).
5. **AES-256-GCM** encrypts + authenticates the payload.
6. Output layout: `HEADER_MAGIC | salt | nonce | ciphertext+tag`
7. Original folder deleted.

### Decryption
1. Magic bytes validated.
2. Key re-derived from stored salt + password.
3. GCM decrypts and **authenticates** — wrong password detected before extraction.
4. tar.gz extracted with path-traversal guard.
5. `.ez` file deleted.

---

## Security

| Property | Detail |
|----------|--------|
| Cipher | AES-256-GCM (authenticated encryption) |
| KDF | PBKDF2-HMAC-SHA256, 600 000 iterations |
| Salt | 256-bit random per encryption |
| Nonce | 96-bit random per encryption |
| Integrity | GCM tag detects wrong passwords and corruption |
| Path safety | Archive members validated before extraction |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [cryptography](https://pypi.org/project/cryptography/) ≥ 50.0.0 | AES-256-GCM via `AESGCM` |
| [typer](https://pypi.org/project/typer/) ≥ 0.27.1 | CLI framework |
| [pytest](https://pypi.org/project/pytest/) ≥ 9.1.1 | Test runner |

**Requires Python ≥ 3.14**
