# Production Build

Build on the same OS you want to ship. Use Windows to create a Windows app, Linux to create a Linux installer, and macOS to create a macOS app and disk image.

## 1. Prepare

Use Python 3.10 for release builds. The app code supports Python 3.10 through 3.12, but the production scripts intentionally default to Python 3.10.

```bash
python -m venv venv
source venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements-dev.txt
```

On Windows PowerShell:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements-dev.txt
```

Install `ffmpeg` separately and make sure it is available on `PATH` for development runs.

## 2. Verify

```bash
python -m pytest -q
python -m meta_video_filter
```

## 3. Build

```bash
python scripts/prepare_yolo_model.py --output build/release-assets/yolov8n.pt
META_VIDEO_FILTER_YOLO_MODEL="$PWD/build/release-assets/yolov8n.pt" \
  pyinstaller MetaVideoFilter.spec --clean --noconfirm
```

The app folder will be written to:

```text
dist/MetaVideoFilter/
```

Run:

```bash
dist/MetaVideoFilter/MetaVideoFilter
```

On Windows:

```powershell
.\dist\MetaVideoFilter\MetaVideoFilter.exe
```

## 4. Windows Installer EXE

Install prerequisites on Windows:

```powershell
winget install Python.Python.3.10
winget install JRSoftware.InnoSetup
```

If you prefer manual downloads:

```text
https://www.python.org/downloads/release/python-310/
https://jrsoftware.org/isinfo.php
```

Then run:

```powershell
.\scripts\build_windows_installer.ps1
```

This will:

- create/use `venv`
- use Python 3.10 by default through the `py -3.10` launcher
- stop if an existing `venv` was created with a different Python version
- install build dependencies
- run tests
- build `dist\MetaVideoFilter\MetaVideoFilter.exe`
- install FFmpeg with `winget` if missing
- copy `ffmpeg.exe` into the app folder so the installed app can use it by itself
- build the installer

The installer will be written to:

```text
release\MetaVideoFilter_Setup_0.1.0.exe
```

If Inno Setup is installed somewhere custom:

```powershell
.\scripts\build_windows_installer.ps1 -InnoSetupCompiler "C:\Path\To\ISCC.exe"
```

If FFmpeg is installed somewhere custom:

```powershell
.\scripts\build_windows_installer.ps1 -FfmpegPath "C:\ffmpeg\bin\ffmpeg.exe"
```

The final Windows installer does not install system Python. PyInstaller embeds the Python runtime inside `MetaVideoFilter.exe`, and the build script bundles `ffmpeg.exe` beside the app, so the installed app can run on its own.

If you do not use the Windows `py` launcher:

```powershell
.\scripts\build_windows_installer.ps1 -Python "C:\Path\To\Python310\python.exe" -PythonArgs @()
```

If you already have a `venv` from another Python version, delete it first:

```powershell
Remove-Item -Recurse -Force .\venv
```

## 5. Linux AppImage

Build a standalone Linux application, equivalent in spirit to the macOS DMG:

```bash
./scripts/build_linux_appimage.sh
```

This creates:

```text
release/MetaVideoFilter-linux-x86_64.AppImage
```

Users run it without installing Python, FFmpeg, or project dependencies:

```bash
chmod +x MetaVideoFilter-linux-x86_64.AppImage
./MetaVideoFilter-linux-x86_64.AppImage
```

The AppImage bundles the Python runtime, FFmpeg, and YOLO model. It targets
x86_64 Linux. For older Linux distributions, build on the oldest supported
distribution to maximize compatibility. It uses CPU-only PyTorch to stay
portable and within GitHub's release-asset size limit.

## 6. Linux Bootstrap Installer

Build the lightweight Linux installer:

```bash
./scripts/build_linux_installer.sh
```

This creates:

```text
release/MetaVideoFilter-linux-source.tar.gz
release/MetaVideoFilter-linux-x86_64.run
```

Install:

```bash
chmod +x release/MetaVideoFilter-linux-x86_64.run
./release/MetaVideoFilter-linux-x86_64.run
```

The Linux installer is intentionally small. It embeds the app source, requires internet access during install, installs missing system tools where possible, forces `python3.10`, creates a private virtual environment, installs `requirements.txt`, installs the app into that environment, creates a desktop launcher entry, and checks for `ffmpeg`.

If missing, the installer automatically tries to install:

- `python3.10` on supported apt/dnf/zypper systems
- `ffmpeg` on supported apt/dnf/zypper/pacman systems
- common Qt/OpenCV runtime libraries on supported systems

Run:

```bash
meta-video-filter
```

Uninstall:

```bash
./release/MetaVideoFilter-linux-x86_64.run --uninstall
```

## 7. macOS App and DMG

Build on a Mac with Xcode Command Line Tools installed:

```bash
xcode-select --install
./scripts/build_macos_installer.sh --arch arm64
```

For an Intel Mac, use `--arch x86_64`. The build creates a self-contained app
bundle and a drag-and-drop disk image:

```text
dist/Meta Video Filter.app
release/MetaVideoFilter-macos-arm64.dmg
```

The app bundles FFmpeg through `imageio-ffmpeg`, so customers do not need
Homebrew, Python, or FFmpeg installed. The pinned version includes a native
Apple Silicon FFmpeg binary. Build a separate DMG for Apple Silicon and Intel
unless you have a universal2 Python environment and dependencies.
The YOLO person-detection model is downloaded and embedded while building, so
the installed app does not need to download it on first launch.

For a distributable release outside your own team, sign and notarize it:

```bash
./scripts/build_macos_installer.sh \
  --arch arm64 \
  --codesign-identity "Developer ID Application: Your Name (TEAMID)" \
  --notary-profile "meta-video-filter-notary"
```

## Notes

- The app uses `ffmpeg` for audio analysis and exports. Desktop builds include a platform-specific FFmpeg binary through `imageio-ffmpeg`; the Linux installer installs Python dependencies at install time instead of bundling them, so the release stays small.
- Release builders download and embed `yolov8n.pt` during the build. Installed Windows, Linux, and macOS apps do not download the person-detection model on first run.
- GitHub Actions can build the Linux AppImage and Windows Setup EXE on their native operating systems. Run **Build Release Installers** manually and provide an existing release tag, or push a new version tag.
- GitHub Actions can build an Apple Silicon DMG with **Build macOS Release** on the `macos-14` ARM runner. It is ad-hoc signed; notarized public releases require Apple Developer signing and notarization credentials.
- PyInstaller builds can be large because Ultralytics depends on PyTorch. Prefer the lightweight Linux installer unless you specifically need offline installation.
- Ultralytics is AGPL-3.0 licensed. Review license obligations before distributing outside your own machine or organization.
