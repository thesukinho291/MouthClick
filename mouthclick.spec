# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
model_file = project_root / "models" / "face_landmarker.task"

a = Analysis(
    ["mouthclick/main.py"],
    pathex=[],
    binaries=[],
    datas=[(str(model_file), "models")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MouthClick",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
