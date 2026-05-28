"""
Click-based command-line interface for ezlock.

Two sub-commands are exposed:
  encrypt (e) - Compress and encrypt a folder → <folder>.ez
  decrypt (d) - Decrypt a .ez file → original folder
"""

import click

from .operations import decrypt_folder, encrypt_folder


# ── Root group ──────────────────────────────────────────────────────────────────

@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
def cli() -> None:
    """
    ezlock — Password-based folder encryption using AES-256-GCM + PBKDF2.

    \b
    Examples:
      ezlock encrypt Documents/
      ezlock decrypt Documents.ez
    """


# ── encrypt command ──────────────────────────────────────────────────────────────

@cli.command("encrypt")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option(
    "-p", "--password",
    default=None,
    help="Encryption password (omit to be prompted securely).",
)
def encrypt_cmd(folder: str, password: str | None) -> None:
    """Encrypt FOLDER and produce FOLDER.ez.

    \b
    You will be prompted for a password unless -p / --password is supplied.
    """
    if password is None:
        password = click.prompt("Enter encryption password", hide_input=True)
        confirm  = click.prompt("Confirm password",          hide_input=True)
        if password != confirm:
            raise click.UsageError("Passwords do not match.")
    if not password:
        raise click.UsageError("Password cannot be empty.")

    try:
        encrypt_folder(folder, password)
    except (FileNotFoundError, NotADirectoryError, FileExistsError) as exc:
        raise click.ClickException(str(exc))


# ── decrypt command ──────────────────────────────────────────────────────────────

@cli.command("decrypt")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    "-p", "--password",
    default=None,
    help="Decryption password (omit to be prompted securely).",
)
def decrypt_cmd(file: str, password: str | None) -> None:
    """Decrypt FILE and restore the original folder.

    \b
    You will be prompted for a password unless -p / --password is supplied.
    """
    if password is None:
        password = click.prompt("Enter decryption password", hide_input=True)
    if not password:
        raise click.UsageError("Password cannot be empty.")

    try:
        decrypt_folder(file, password)
    except (FileNotFoundError, IsADirectoryError, FileExistsError) as exc:
        raise click.ClickException(str(exc))
    except ValueError as exc:
        raise click.ClickException(str(exc))
