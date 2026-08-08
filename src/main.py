import typer
from pathlib import Path

from operations import decrypt_folder, encrypt_folder


app = typer.Typer(help="Encrypt and decrypt folders.")


@app.command()
def encrypt(source_path: Path, password: str):
    """Encrypt a folder.
    
    Args:
        source_path (Path): Path of the folder to encrypt.
        password (str): Password to encrypt the folder with.
    """

    try:
        encrypt_folder(source_path, password)
    except (FileNotFoundError, NotADirectoryError, FileExistsError) as exc:
        print(f"[ezlock] {exc}")
    except Exception as exc:
        raise exc


@app.command()
def decrypt(source_path: Path, password: str):
    """Decrypt a file and restore original folder.
    
    Args:
        source_path (Path): Path of the file to decrypt.
        password (str): Password to decrypt the file with.
    """

    try:
        decrypt_folder(source_path, password)
    except (FileNotFoundError, IsADirectoryError, FileExistsError) as exc:
        print(f"[ezlock] {exc}")
    except Exception as exc:
        raise exc


if __name__ == '__main__':
    app()
