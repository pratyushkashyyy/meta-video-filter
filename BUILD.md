# Production Build

Build on the same OS you want to ship. Use Windows to create a Windows app and Linux to create a Linux app.

## 1. Prepare

Use Python 3.10, 3.11, or 3.12.

```bash
python -m venv venv
source venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements-dev.txt
```

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements-dev.txt
```

Install `ffmpeg` separately and make sure it is available on `PATH`.

## 2. Verify

```bash
python -m pytest -q
python -m meta_video_filter
```

## 3. Build

```bash
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

Install Inno Setup 6 on Windows:

```text
https://jrsoftware.org/isinfo.php
```

Then run:

```powershell
.\scripts\build_windows_installer.ps1
```

This will:

- create/use `venv`
- install build dependencies
- run tests
- build `dist\MetaVideoFilter\MetaVideoFilter.exe`
- build the installer

The installer will be written to:

```text
release\MetaVideoFilter_Setup_0.1.0.exe
```

If Inno Setup is installed somewhere custom:

```powershell
.\scripts\build_windows_installer.ps1 -InnoSetupCompiler "C:\Path\To\ISCC.exe"
```

## 5. Linux Installer

After building with PyInstaller on Linux:

```bash
./scripts/build_linux_installer.sh
```

This creates:

```text
release/MetaVideoFilter-linux-x86_64.tar.gz
release/MetaVideoFilter-linux-x86_64.run
```

Install:

```bash
chmod +x release/MetaVideoFilter-linux-x86_64.run
./release/MetaVideoFilter-linux-x86_64.run
```

Run:

```bash
meta-video-filter
```

Uninstall:

```bash
./release/MetaVideoFilter-linux-x86_64.run --uninstall
```

## Notes

- The app uses `ffmpeg` for audio analysis and exports. The packaged app expects `ffmpeg` on `PATH`.
- YOLO may download `yolov8n.pt` the first time it runs if the model file is not already present.
- Build artifacts can be large because Ultralytics depends on PyTorch.
- Ultralytics is AGPL-3.0 licensed. Review license obligations before distributing outside your own machine or organization.
