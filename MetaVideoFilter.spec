# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += ["backports", "backports.tarfile"]
hiddenimports += collect_submodules("ultralytics")
hiddenimports += collect_submodules("imageio_ffmpeg")

datas = []
datas += collect_data_files("ultralytics")
datas += collect_data_files("imageio_ffmpeg")
datas += [
    ("meta_video_filter/assets/app_icon.png", "meta_video_filter/assets"),
    ("meta_video_filter/assets/app_icon.ico", "meta_video_filter/assets"),
]

yolo_model = os.environ.get("META_VIDEO_FILTER_YOLO_MODEL")
if not yolo_model or not os.path.isfile(yolo_model):
    raise RuntimeError(
        "Set META_VIDEO_FILTER_YOLO_MODEL to the prepared yolov8n.pt file before building a release."
    )
datas.append((yolo_model, "meta_video_filter/assets/models"))

if sys.platform == "darwin":
    icon_file = os.environ.get("METAVIDEOFILTER_MAC_ICON")
    if not icon_file:
        raise RuntimeError(
            "Set METAVIDEOFILTER_MAC_ICON to an .icns file when building on macOS."
        )
else:
    icon_file = "meta_video_filter/assets/app_icon.ico"

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
    icon=icon_file,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=os.environ.get("PYINSTALLER_TARGET_ARCH") or None,
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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Meta Video Filter.app",
        icon=icon_file,
        bundle_identifier="com.metavideofilter.app",
        info_plist={
            "CFBundleDisplayName": "Meta Video Filter",
            "CFBundleName": "Meta Video Filter",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
        },
    )
