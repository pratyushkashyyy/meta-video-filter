#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="$ROOT_DIR/release"
ARCHIVE="$RELEASE_DIR/MetaVideoFilter-linux-source.tar.gz"
INSTALLER="$RELEASE_DIR/MetaVideoFilter-linux-x86_64.run"

mkdir -p "$RELEASE_DIR"
rm -f "$ARCHIVE" "$INSTALLER"

git -C "$ROOT_DIR" archive --format=tar.gz --prefix=source/ -o "$ARCHIVE" HEAD

cat > "$INSTALLER" <<'INSTALLER_HEADER'
#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Meta Video Filter"
APP_ID="meta-video-filter"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/MetaVideoFilter"
SOURCE_DIR="$INSTALL_DIR/source"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/${APP_ID}.desktop"
LAUNCHER="$BIN_DIR/meta-video-filter"
ICON_FILE="$SOURCE_DIR/meta_video_filter/assets/app_icon.png"
PYTHON_BIN="python3.10"

usage() {
    cat <<USAGE
Meta Video Filter Linux Installer

Usage:
  ./MetaVideoFilter-linux-x86_64.run
  ./MetaVideoFilter-linux-x86_64.run --uninstall

Requires:
  Internet access during install
  Python 3.10

Installs to:
  $INSTALL_DIR

Creates:
  $LAUNCHER
  $DESKTOP_FILE
USAGE
}

confirm() {
    local prompt="$1"
    local answer

    if [[ ! -t 0 ]]; then
        return 1
    fi

    read -r -p "$prompt [Y/n] " answer
    case "${answer:-Y}" in
        y|Y|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

install_with_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y "$@"
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y "$@"
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y "$@"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --needed "$@"
    else
        return 1
    fi
}

install_python310() {
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        return 0
    fi

    echo "Python 3.10 is required and was not found."
    if ! confirm "Install Python 3.10 with your system package manager?"; then
        echo "Install python3.10 manually, then run this installer again."
        exit 1
    fi

    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3.10 python3.10-devel
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python310 python310-devel
    else
        echo "Could not automatically install Python 3.10 on this distro."
        echo "Install python3.10 manually, then run this installer again."
        exit 1
    fi

    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        echo "Python 3.10 still was not found after package install."
        exit 1
    fi
}

install_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1; then
        return 0
    fi

    echo "ffmpeg is required for audio analysis and video export."
    if ! confirm "Install ffmpeg with your system package manager?"; then
        echo "Install ffmpeg manually, then run this installer again."
        exit 1
    fi

    if ! install_with_package_manager ffmpeg; then
        echo "Could not automatically install ffmpeg."
        echo "Install ffmpeg manually, then run this installer again."
        exit 1
    fi
}

install_linux_runtime_libs() {
    if ! confirm "Install common Qt/OpenCV runtime libraries if available?"; then
        return 0
    fi

    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y libgl1 libglib2.0-0 libxcb-cursor0 libxcb-xinerama0
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y mesa-libGL glib2 xcb-util-cursor
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y Mesa-libGL1 glib2-tools xcb-util-cursor
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --needed mesa glib2 xcb-util-cursor
    fi
}

uninstall_app() {
    rm -rf "$INSTALL_DIR"
    rm -f "$LAUNCHER"
    rm -f "$DESKTOP_FILE"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
    fi
    echo "Uninstalled $APP_NAME"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

if [[ "${1:-}" == "--uninstall" ]]; then
    uninstall_app
    exit 0
fi

if ! command -v tar >/dev/null 2>&1; then
    echo "tar is required to install $APP_NAME"
    exit 1
fi

install_python310
install_ffmpeg
install_linux_runtime_libs

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

ARCHIVE_LINE="$(awk '/^__META_VIDEO_FILTER_ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' "$0")"
tail -n +"$ARCHIVE_LINE" "$0" | tar -xz -C "$INSTALL_DIR"

"$PYTHON_BIN" -m venv "$VENV_DIR" || {
    echo "Could not create a Python 3.10 virtual environment."
    echo "On Debian/Ubuntu, install python3.10-venv and run this installer again."
    exit 1
}

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/python" -m pip install -r "$SOURCE_DIR/requirements.txt"
"$VENV_DIR/bin/python" -m pip install --no-deps "$SOURCE_DIR"

cat > "$LAUNCHER" <<LAUNCH
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m meta_video_filter "\$@"
LAUNCH
chmod +x "$LAUNCHER"

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Meta Video Filter
Comment=Rank, crop, and export Meta ad videos
Exec=$LAUNCHER
Icon=$ICON_FILE
Terminal=false
Categories=AudioVideo;Video;Utility;
StartupNotify=true
DESKTOP

chmod +x "$DESKTOP_FILE"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "$APP_NAME installed."
echo "Run it with: meta-video-filter"
echo "If that command is not found, add $BIN_DIR to PATH."
echo "Uninstall with: $0 --uninstall"
exit 0

__META_VIDEO_FILTER_ARCHIVE_BELOW__
INSTALLER_HEADER

cat "$ARCHIVE" >> "$INSTALLER"
chmod +x "$INSTALLER"

du -h "$ARCHIVE" "$INSTALLER"
echo "Linux installer created: $INSTALLER"
