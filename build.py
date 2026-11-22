"""Builds the standalone game with PyInstaller.

Run it on the operating system you want to build for (a Windows build
must be made on Windows):  python build.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
GAME = DIST / "Pacman"
EXTRA_FILES = ("config.json", "PLAYER_README.txt")


def main() -> int:
    """Build the game folder and a zip ready to upload."""
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm",
               "--clean", "pacman.spec"]
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}\n"
              "Is PyInstaller installed? (pip install pyinstaller)",
              file=sys.stderr)
        return 1
    for name in EXTRA_FILES:
        shutil.copy(ROOT / name, GAME / name)
    archive = shutil.make_archive(str(GAME), "zip", root_dir=DIST,
                                  base_dir="Pacman")
    print(f"Game folder: {GAME}\nZip to upload: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
