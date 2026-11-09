#!/usr/bin/env bash
# Script to build a standalone Theme-Hub-x86_64.AppImage
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPDIR="/tmp/theme-hub.AppDir"
DIST_DIR="$SCRIPT_DIR/dist"

echo "=========================================="
echo " Building Theme Hub AppImage"
echo "=========================================="

mkdir -p "$DIST_DIR"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/theme-hub"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APPDIR/usr/lib/python3/dist-packages"

# 1. Install app files into AppDir
cp -r "$SCRIPT_DIR/src/theme_hub" "$APPDIR/usr/lib/python3/dist-packages/"
install -m 755 "$SCRIPT_DIR/src/bin/theme-hub" "$APPDIR/usr/bin/theme-hub"
install -m 755 "$SCRIPT_DIR/src/bin/theme-hub-cli" "$APPDIR/usr/bin/theme-hub-cli"
cp -r "$SCRIPT_DIR/assets/"* "$APPDIR/usr/share/theme-hub/"
install -m 644 "$SCRIPT_DIR/data/io.github.themehub.desktop" "$APPDIR/io.github.themehub.desktop"
install -m 644 "$SCRIPT_DIR/data/io.github.themehub.desktop" "$APPDIR/usr/share/applications/io.github.themehub.desktop"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.svg" "$APPDIR/io.github.themehub.svg"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/io.github.themehub.svg"
install -m 644 "$SCRIPT_DIR/assets/branding/io.github.themehub.png" "$APPDIR/.DirIcon"

# 2. Create AppRun launcher
cat << 'EOF' > "$APPDIR/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
exec "${HERE}/usr/bin/theme-hub" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 3. Download appimagetool if not available
APPIMAGETOOL="/tmp/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    curl -sSL "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -o "$APPIMAGETOOL" || true
    chmod +x "$APPIMAGETOOL" 2>/dev/null || true
fi

if [ -x "$APPIMAGETOOL" ]; then
    ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$DIST_DIR/Theme-Hub-x86_64.AppImage"
    echo "✓ AppImage successfully generated: $DIST_DIR/Theme-Hub-x86_64.AppImage"
else
    echo "Note: AppDir structure prepared at $APPDIR."
    echo "Run with appimagetool to generate final binary."
fi
