# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe: python build.py   (or: make package)
a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=["mazegenerator"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Pacman",
    console=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Pacman",
)
