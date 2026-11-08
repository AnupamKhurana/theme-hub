#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="system"

for arg in "$@"; do
    case "$arg" in
        --user)
            MODE="user"
            ;;
        --system)
            MODE="system"
            ;;
        --help|-h)
            echo "Theme Hub Installer"
            echo "Usage: ./install.sh [--user | --system]"
            echo ""
            echo "Options:"
            echo "  --user    Install into ~/.local (no root required)"
            echo "  --system  Install into /usr/local (requires sudo/root)"
            exit 0
            ;;
    esac
done

if [ "$MODE" = "system" ] && [ "$(id -u)" -ne 0 ]; then
    echo "Warning: Installing system-wide requires root privileges."
    echo "Rerunning with sudo..."
    exec sudo "$0" --system
fi

echo "=========================================="
echo " Installing Theme Hub ($MODE mode)..."
echo "=========================================="

if [ "$MODE" = "system" ]; then
    PREFIX="/usr/local"
    BIN_DIR="$PREFIX/bin"
    SHARE_DIR="$PREFIX/share"
    PY_DIR="/usr/local/lib/python3/dist-packages"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor"
else
    PREFIX="$HOME/.local"
    BIN_DIR="$PREFIX/bin"
    SHARE_DIR="$PREFIX/share"
    PY_DIR="$PREFIX/lib/python3/dist-packages"
    DESKTOP_DIR="$PREFIX/share/applications"
    ICON_DIR="$PREFIX/share/icons/hicolor"
fi

mkdir -p "$BIN_DIR"
mkdir -p "$SHARE_DIR/theme-hub"
mkdir -p "$PY_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR/scalable/apps"
mkdir -p "$ICON_DIR/128x128/apps"
mkdir -p "$ICON_DIR/64x64/apps"

# 1. Install executables
echo "Installing executables to $BIN_DIR..."
install -m 755 "$SCRIPT_DIR/src/bin/theme-hub" "$BIN_DIR/theme-hub"
install -m 755 "$SCRIPT_DIR/src/bin/theme-hub-cli" "$BIN_DIR/theme-hub-cli"

# 2. Install python library
echo "Installing python package to $PY_DIR..."
rm -rf "$PY_DIR/theme_hub"
cp -r "$SCRIPT_DIR/src/theme_hub" "$PY_DIR/"

# 3. Install desktop launcher
echo "Installing desktop launcher..."
install -m 644 "$SCRIPT_DIR/data/io.github.themehub.desktop" "$DESKTOP_DIR/io.github.themehub.desktop"

# 4. Install icons
echo "Installing application icons..."
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.svg" "$ICON_DIR/scalable/apps/io.github.themehub.svg"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.png" "$ICON_DIR/128x128/apps/io.github.themehub.png"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub-64.png" "$ICON_DIR/64x64/apps/io.github.themehub-64.png"

# 5. Install assets
echo "Installing theme assets (wallpapers, cursors, fonts, icons)..."
cp -r "$SCRIPT_DIR/assets/"* "$SHARE_DIR/theme-hub/"

# Link fonts into font directories
if [ "$MODE" = "system" ]; then
    mkdir -p /usr/share/fonts/truetype/theme-hub
    cp -rn "$SCRIPT_DIR/assets/fonts/"* /usr/share/fonts/truetype/theme-hub/ 2>/dev/null || true
    fc-cache -f /usr/share/fonts/truetype/theme-hub 2>/dev/null || true
else
    mkdir -p "$HOME/.local/share/fonts"
    cp -rn "$SCRIPT_DIR/assets/fonts/"* "$HOME/.local/share/fonts/" 2>/dev/null || true
    fc-cache -f "$HOME/.local/share/fonts" 2>/dev/null || true
fi

# Refresh desktop & icon databases
if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q "$DESKTOP_DIR" || true
fi

if which gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f "$ICON_DIR" 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "✓ Theme Hub successfully installed!"
echo "  Run via App Menu: 'Theme Hub'"
echo "  Run via Terminal: 'theme-hub' or 'theme-hub-cli list'"
echo "=========================================="
