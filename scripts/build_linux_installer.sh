#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/dist/MetaVideoFilter"
RELEASE_DIR="$ROOT_DIR/release"
ARCHIVE="$RELEASE_DIR/MetaVideoFilter-linux-x86_64.tar.gz"
INSTALLER="$RELEASE_DIR/MetaVideoFilter-linux-x86_64.run"

if [[ ! -x "$APP_DIR/MetaVideoFilter" ]]; then
    echo "Missing built app at $APP_DIR"
    echo "Run: ./venv/bin/pyinstaller MetaVideoFilter.spec --clean --noconfirm"
    exit 1
fi

mkdir -p "$RELEASE_DIR"

if [[ ! -f "$ARCHIVE" ]]; then
    tar -czf "$ARCHIVE" -C "$ROOT_DIR/dist" MetaVideoFilter
fi

cat > "$INSTALLER" <<'INSTALLER_HEADER'
#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Meta Video Filter"
APP_ID="meta-video-filter"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/MetaVideoFilter"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/${APP_ID}.desktop"

usage() {
    cat <<USAGE
Meta Video Filter Linux Installer

Usage:
  ./MetaVideoFilter-linux-x86_64.run
  ./MetaVideoFilter-linux-x86_64.run --uninstall

Installs to:
  $INSTALL_DIR

Creates:
  $BIN_DIR/meta-video-filter
  $DESKTOP_FILE
USAGE
}

uninstall_app() {
    rm -rf "$INSTALL_DIR"
    rm -f "$BIN_DIR/meta-video-filter"
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

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

ARCHIVE_LINE="$(awk '/^__META_VIDEO_FILTER_ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' "$0")"
tail -n +"$ARCHIVE_LINE" "$0" | tar -xz -C "$(dirname "$INSTALL_DIR")"

chmod +x "$INSTALL_DIR/MetaVideoFilter"
ln -sf "$INSTALL_DIR/MetaVideoFilter" "$BIN_DIR/meta-video-filter"

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Meta Video Filter
Comment=Rank, crop, and export Meta ad videos
Exec=$INSTALL_DIR/MetaVideoFilter
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
