#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-macos"
BUILD_DIR="$ROOT_DIR/build/macos"
RELEASE_DIR="$ROOT_DIR/release"
PYTHON_BIN="python3.10"
TARGET_ARCH=""
CODESIGN_IDENTITY=""
NOTARY_PROFILE=""

usage() {
    cat <<'USAGE'
Build a macOS Meta Video Filter application and DMG.

Usage:
  ./scripts/build_macos_installer.sh [options]

Options:
  --python PATH              Python 3.10 executable (default: python3.10)
  --arch ARCH                arm64, x86_64, or universal2
  --codesign-identity NAME   Apple Developer signing identity
  --notary-profile NAME      Keychain profile for xcrun notarytool

Build this on a Mac. Apple Silicon builds should use --arch arm64; Intel builds
should use --arch x86_64. A universal2 release requires a universal2 Python and
universal dependencies.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --python) PYTHON_BIN="$2"; shift 2 ;;
        --arch) TARGET_ARCH="$2"; shift 2 ;;
        --codesign-identity) CODESIGN_IDENTITY="$2"; shift 2 ;;
        --notary-profile) NOTARY_PROFILE="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

if [[ -n "$TARGET_ARCH" && ! "$TARGET_ARCH" =~ ^(arm64|x86_64|universal2)$ ]]; then
    echo "--arch must be arm64, x86_64, or universal2." >&2
    exit 1
fi

if [[ -n "$NOTARY_PROFILE" && -z "$CODESIGN_IDENTITY" ]]; then
    echo "Notarization requires --codesign-identity." >&2
    exit 1
fi

cd "$ROOT_DIR"

for command in sips iconutil hdiutil codesign ditto; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "'$command' is required. Install Xcode Command Line Tools with: xcode-select --install" >&2
        exit 1
    fi
done

PYTHON_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PYTHON_VERSION" != "3.10" ]]; then
    echo "Python 3.10 is required; got Python $PYTHON_VERSION." >&2
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_VERSION="$($VENV_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$VENV_VERSION" != "3.10" ]]; then
    echo "$VENV_DIR was created with Python $VENV_VERSION. Remove it and run again." >&2
    exit 1
fi

"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel
"$VENV_PYTHON" -m pip install -r requirements-dev.txt
"$VENV_PYTHON" -m pytest -q

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/icon.iconset" "$RELEASE_DIR"

create_icon() {
    local size="$1"
    local name="$2"
    sips -z "$size" "$size" meta_video_filter/assets/app_icon.png --out "$BUILD_DIR/icon.iconset/$name" >/dev/null
}

create_icon 16 icon_16x16.png
create_icon 32 icon_16x16@2x.png
create_icon 32 icon_32x32.png
create_icon 64 icon_32x32@2x.png
create_icon 128 icon_128x128.png
create_icon 256 icon_128x128@2x.png
create_icon 256 icon_256x256.png
create_icon 512 icon_256x256@2x.png
create_icon 512 icon_512x512.png
create_icon 1024 icon_512x512@2x.png
iconutil -c icns "$BUILD_DIR/icon.iconset" -o "$BUILD_DIR/MetaVideoFilter.icns"

export METAVIDEOFILTER_MAC_ICON="$BUILD_DIR/MetaVideoFilter.icns"
export PYINSTALLER_TARGET_ARCH="$TARGET_ARCH"

"$VENV_DIR/bin/pyinstaller" MetaVideoFilter.spec --clean --noconfirm

APP_BUNDLE="$ROOT_DIR/dist/Meta Video Filter.app"
if [[ ! -d "$APP_BUNDLE" ]]; then
    echo "Expected macOS app bundle was not created: $APP_BUNDLE" >&2
    exit 1
fi

if [[ -n "$CODESIGN_IDENTITY" ]]; then
    codesign --force --deep --options runtime --sign "$CODESIGN_IDENTITY" "$APP_BUNDLE"
else
    codesign --force --deep --sign - "$APP_BUNDLE"
fi
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"

ARCH_LABEL="${TARGET_ARCH:-$(uname -m)}"
DMG_PATH="$RELEASE_DIR/MetaVideoFilter-macos-$ARCH_LABEL.dmg"
DMG_STAGING="$BUILD_DIR/dmg"
rm -f "$DMG_PATH"
mkdir -p "$DMG_STAGING"
ditto "$APP_BUNDLE" "$DMG_STAGING/Meta Video Filter.app"
ln -s /Applications "$DMG_STAGING/Applications"
hdiutil create -volname "Meta Video Filter" -srcfolder "$DMG_STAGING" -ov -format UDZO "$DMG_PATH"

if [[ -n "$NOTARY_PROFILE" ]]; then
    xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_PROFILE" --wait
    xcrun stapler staple "$DMG_PATH"
fi

echo "macOS installer created: $DMG_PATH"
