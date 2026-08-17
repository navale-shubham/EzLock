import typer
from pathlib import Path
from getpass import getpass
from operations import decrypt_folder, encrypt_folder


app = typer.Typer(
    help="Encrypt and decrypt folders.",
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False
)


@app.command()
def encrypt(source_path: Path):
    """Encrypt a folder.
    
    Args:
        source_path (Path): Path of the folder to encrypt.
    """

    password = getpass("Enter password: ", echo_char='*')
    confirm_password = getpass("Confirm password: ", echo_char='*')

    if password != confirm_password:
        print("Passwords do not match.")
        return

    try:
        encrypt_folder(source_path, password)
    except (FileNotFoundError, NotADirectoryError, FileExistsError) as exc:
        print(f"{exc}")
    except Exception as exc:
        print(f"Error: {exc}")


@app.command()
def decrypt(source_path: Path):
    """Decrypt a file and restore original folder.
    
    Args:
        source_path (Path): Path of the file to decrypt.
    """

    password = getpass("Enter password: ", echo_char='*')

    try:
        decrypt_folder(source_path, password)
    except (FileNotFoundError, IsADirectoryError, FileExistsError) as exc:
        print(f"{exc}")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == '__main__':
    app()
