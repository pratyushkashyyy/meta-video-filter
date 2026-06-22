# Meta Video Filter

Cross-platform Python Qt desktop app for ranking short ad videos and exporting Group A/B picks to a fixed Meta Reels format.

## Setup

Use Python 3.10, 3.11, or 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install `ffmpeg` and make sure it is available on `PATH`.

## GPU

The desktop app has controls for person-detection device and video-export encoder. YOLO person detection automatically uses `cuda:0` when PyTorch can see a CUDA GPU. Otherwise it falls back to CPU.

To force a device:

```bash
META_VIDEO_FILTER_DEVICE=cuda:0 python -m meta_video_filter
META_VIDEO_FILTER_DEVICE=cpu python -m meta_video_filter
```

On Windows PowerShell:

```powershell
$env:META_VIDEO_FILTER_DEVICE="cuda:0"
python -m meta_video_filter
```

Aspect-ratio video export also uses GPU encoding automatically when CUDA is available and FFmpeg supports NVIDIA NVENC. It falls back to CPU `libx264` if GPU encoding is unavailable or fails.

To force the export encoder:

```bash
META_VIDEO_FILTER_VIDEO_ENCODER=h264_nvenc python -m meta_video_filter
META_VIDEO_FILTER_VIDEO_ENCODER=cpu python -m meta_video_filter
```

The CLI also supports explicit choices:

```bash
python bestpicket.py /path/to/videos --yolo-device cpu --video-encoder h264_nvenc
```

## Run

```bash
python -m meta_video_filter
```

The app lets you choose an input folder and writes everything inside `Meta_Ad_Output` in the selected input folder: CSV report, thumbnails, Group A/B folders, a later folder, and optimized `9:16` Reels exports at `1080x1920`.

## Legacy CLI

The original `bestpicket.py` entrypoint now accepts an input folder instead of a hardcoded Windows path. Output is written inside that folder as `Meta_Ad_Output`:

```bash
python bestpicket.py /path/to/videos
```

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

## Production Build

See [BUILD.md](BUILD.md) for PyInstaller packaging instructions.

Windows installer support is included through Inno Setup. On Windows, install Python 3.10 and Inno Setup 6 first:

```powershell
winget install Python.Python.3.10
winget install JRSoftware.InnoSetup
```

Then build:

```powershell
.\scripts\build_windows_installer.ps1
```

The build script installs FFmpeg with `winget` if missing, bundles `ffmpeg.exe` beside the app, and PyInstaller embeds Python in the final `.exe`.

Linux installer support:

```bash
./scripts/build_linux_installer.sh
./release/MetaVideoFilter-linux-x86_64.run
```
