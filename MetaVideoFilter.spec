# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += ["backports", "backports.tarfile"]
hiddenimports += collect_submodules("ultralytics")

datas = []
datas += collect_data_files("ultralytics")
datas += [
    ("meta_video_filter/assets/app_icon.png", "meta_video_filter/assets"),
    ("meta_video_filter/assets/app_icon.ico", "meta_video_filter/assets"),
]

a = Analysis(
    ["build_entry.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MetaVideoFilter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="meta_video_filter/assets/app_icon.ico",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MetaVideoFilter",
)
