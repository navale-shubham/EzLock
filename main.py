"""
python main.py encrypt Documents/
python main.py decrypt Documents.ez
"""

# pyrefly: ignore [missing-import]
from src.ezlock.cli import cli

if __name__ == "__main__":
    cli()
