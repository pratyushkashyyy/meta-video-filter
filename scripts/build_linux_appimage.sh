#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-linux"
BUILD_DIR="$ROOT_DIR/build/linux-appimage"
RELEASE_DIR="$ROOT_DIR/release"
PYTHON_BIN="${PYTHON_BIN:-python3.10}"
APPIMAGETOOL_BIN="${APPIMAGETOOL:-appimagetool}"
APP_NAME="Meta Video Filter"
APP_ID="meta-video-filter"
APPDIR="$BUILD_DIR/AppDir"
OUTPUT="$RELEASE_DIR/MetaVideoFilter-linux-x86_64.AppImage"

if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "This builder currently produces x86_64 AppImages only." >&2
    exit 1
fi

cd "$ROOT_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.10 is required. Set PYTHON_BIN to its executable path." >&2
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
PYTHON_VERSION="$($VENV_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PYTHON_VERSION" != "3.10" ]]; then
    echo "$VENV_DIR uses Python $PYTHON_VERSION. Remove it and rebuild with Python 3.10." >&2
    exit 1
fi

"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel
"$VENV_PYTHON" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
"$VENV_PYTHON" -m pip install -r requirements-dev.txt
"$VENV_PYTHON" -m pytest -q

rm -rf "$BUILD_DIR" "$ROOT_DIR/dist/MetaVideoFilter"
mkdir -p "$BUILD_DIR" "$RELEASE_DIR"
export META_VIDEO_FILTER_YOLO_MODEL="$("$VENV_PYTHON" scripts/prepare_yolo_model.py --output "$BUILD_DIR/yolov8n.pt")"
"$VENV_DIR/bin/pyinstaller" MetaVideoFilter.spec --clean --noconfirm

if ! command -v "$APPIMAGETOOL_BIN" >/dev/null 2>&1; then
    APPIMAGETOOL_BIN="$BUILD_DIR/appimagetool-x86_64.AppImage"
    curl -fsSL \
        https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
        -o "$APPIMAGETOOL_BIN"
    chmod +x "$APPIMAGETOOL_BIN"
fi

rm -rf "$APPDIR" "$OUTPUT"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -a "$ROOT_DIR/dist/MetaVideoFilter" "$APPDIR/usr/lib/MetaVideoFilter"
cp meta_video_filter/assets/app_icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
cp meta_video_filter/assets/app_icon.png "$APPDIR/$APP_ID.png"

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f "$0")")"
export QT_SCALE_FACTOR_ROUNDING_POLICY="${QT_SCALE_FACTOR_ROUNDING_POLICY:-Round}"
exec "$HERE/usr/lib/MetaVideoFilter/MetaVideoFilter" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/$APP_ID.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Rank, crop, and export Meta ad videos
Exec=MetaVideoFilter
Icon=$APP_ID
Categories=AudioVideo;Video;Utility;
Terminal=false
StartupNotify=true
DESKTOP
cp "$APPDIR/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL_BIN" "$APPDIR" "$OUTPUT"
chmod +x "$OUTPUT"
APPIMAGE_SIZE="$(stat -c %s "$OUTPUT")"
if (( APPIMAGE_SIZE >= 2147483648 )); then
    echo "The AppImage is larger than GitHub Releases' 2 GB asset limit." >&2
    exit 1
fi
echo "Linux AppImage created: $OUTPUT"
