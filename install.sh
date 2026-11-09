#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="system"
DESTDIR=""

while [ $# -gt 0 ]; do
    case "$1" in
        --user)
            MODE="user"
            shift
            ;;
        --system)
            MODE="system"
            shift
            ;;
        --destdir)
            DESTDIR="$2"
            shift 2
            ;;
        --destdir=*)
            DESTDIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Theme Hub Installer"
            echo "Usage: ./install.sh [--user | --system] [--destdir DIR]"
            echo ""
            echo "Options:"
            echo "  --user         Install into ~/.local (no root required)"
            echo "  --system       Install into /usr/local (requires sudo/root)"
            echo "  --destdir DIR  Staged install root for packaging (e.g. PKGBUILD, rpmbuild)"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

if [ "$MODE" = "system" ] && [ -z "$DESTDIR" ] && [ "$(id -u)" -ne 0 ]; then
    echo "Warning: Installing system-wide requires root privileges."
    echo "Rerunning with sudo..."
    exec sudo "$0" --system
fi

echo "=========================================="
echo " Installing Theme Hub ($MODE mode)..."
echo "=========================================="

if [ "$MODE" = "system" ]; then
    PREFIX="${DESTDIR}/usr/local"
    BIN_DIR="$PREFIX/bin"
    SHARE_DIR="$PREFIX/share"
    PY_DIR="${DESTDIR}$(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))" 2>/dev/null || echo "/usr/local/lib/python3/dist-packages")"
    DESKTOP_DIR="${DESTDIR}/usr/share/applications"
    ICON_DIR="${DESTDIR}/usr/share/icons/hicolor"
    FONT_DIR="${DESTDIR}/usr/share/fonts/truetype/theme-hub"
else
    PREFIX="${DESTDIR}${HOME}/.local"
    BIN_DIR="$PREFIX/bin"
    SHARE_DIR="$PREFIX/share"
    PY_DIR="${DESTDIR}$(python3 -c "import site; print(site.getusersitepackages())" 2>/dev/null || echo "$PREFIX/lib/python3/dist-packages")"
    PY_DIST_DIR="$PREFIX/lib/python3/dist-packages"
    DESKTOP_DIR="$PREFIX/share/applications"
    ICON_DIR="$PREFIX/share/icons/hicolor"
    FONT_DIR="${DESTDIR}${HOME}/.local/share/fonts"
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
if [ -n "$PY_DIST_DIR" ] && [ "$PY_DIST_DIR" != "$PY_DIR" ]; then
    mkdir -p "$PY_DIST_DIR"
    rm -rf "$PY_DIST_DIR/theme_hub"
    cp -r "$SCRIPT_DIR/src/theme_hub" "$PY_DIST_DIR/"
fi

# 3. Install desktop launcher
echo "Installing desktop launcher..."
install -m 644 "$SCRIPT_DIR/data/io.github.themehub.desktop" "$DESKTOP_DIR/io.github.themehub.desktop"
[ -f "$SCRIPT_DIR/data/launchpad.desktop" ] && install -m 644 "$SCRIPT_DIR/data/launchpad.desktop" "$DESKTOP_DIR/launchpad.desktop"

# 4. Install icons
echo "Installing application icons..."
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.svg" "$ICON_DIR/scalable/apps/io.github.themehub.svg"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.png" "$ICON_DIR/128x128/apps/io.github.themehub.png"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub-64.png" "$ICON_DIR/64x64/apps/io.github.themehub-64.png"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/macos-launchpad.svg" ] && install -m 644 "$SCRIPT_DIR/assets/icons/custom-launchers/macos-launchpad.svg" "$ICON_DIR/scalable/apps/macos-launchpad.svg"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/apple-logo.svg" ] && install -m 644 "$SCRIPT_DIR/assets/icons/custom-launchers/apple-logo.svg" "$ICON_DIR/scalable/apps/apple-logo.svg"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/windows11-start.svg" ] && install -m 644 "$SCRIPT_DIR/assets/icons/custom-launchers/windows11-start.svg" "$ICON_DIR/scalable/apps/windows11-start.svg"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/modern-start.svg" ] && install -m 644 "$SCRIPT_DIR/assets/icons/custom-launchers/modern-start.svg" "$ICON_DIR/scalable/apps/modern-start.svg"

# 5. Install assets
echo "Installing theme assets (wallpapers, cursors, fonts, icons)..."
rm -rf "$SHARE_DIR/theme-hub"
mkdir -p "$SHARE_DIR/theme-hub"
cp -r "$SCRIPT_DIR/assets/"* "$SHARE_DIR/theme-hub/"

# Link fonts into font directories
mkdir -p "$FONT_DIR"
cp -rn "$SCRIPT_DIR/assets/fonts/"* "$FONT_DIR/" 2>/dev/null || true
if [ -z "$DESTDIR" ]; then
    fc-cache -f "$FONT_DIR" 2>/dev/null || true
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
