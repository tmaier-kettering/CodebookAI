import sys, os
from pathlib import Path


def asset_path(*parts) -> str:
    # When frozen (PyInstaller --onefile), files are unpacked into sys._MEIPASS
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base.joinpath("assets", *parts))