# ezlock — Folder Encryption CLI

Encrypt and decrypt entire folders with a single command.  
Uses **AES-256-GCM** (authenticated encryption) with a **PBKDF2-derived key**.

---

## Project Structure

```
ezlock_project/
├── main.py                   # Entry point  →  python main.py <command>
├── pyproject.toml            # Package metadata
└── src/
    └── ezlock/
        ├── __init__.py       # Public API surface
        ├── cli.py            # Click commands (encrypt / decrypt)
        ├── operations.py     # High-level workflows
        ├── crypto.py         # AES-256-GCM + PBKDF2 key derivation
        ├── archive.py        # tar.gz compress / safe-extract
        └── constants.py      # Shared magic values
```

---

## Quick Start

```bash
# Install dependencies
uv sync

# Run directly
python main.py encrypt Documents/
python main.py decrypt Documents.ez

```

---

## CLI Reference

```
ezlock encrypt [OPTIONS] FOLDER
ezlock decrypt [OPTIONS] FILE
```

| Option | Description |
|--------|-------------|
| `-p, --password TEXT` | Supply password inline (omit for secure prompt) |
| `-h, --help` | Show help and exit |

**Examples:**
```bash
# Password prompt
ezlock encrypt ~/Documents
ezlock decrypt ~/Documents.ez

# Inline password 
ezlock encrypt secrets/ -p "my passphrase"
ezlock decrypt secrets.ez  -p "my passphrase"
```

---

## How It Works

### Encryption
1. Folder → in-memory **tar.gz** (never touches disk unencrypted).
2. Metadata header `{"folder_name": "..."}` prepended so the name survives renaming.
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
