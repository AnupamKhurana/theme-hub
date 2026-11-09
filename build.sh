#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build/deb-root"
DIST_DIR="$SCRIPT_DIR/dist"
PKG_VERSION="1.0.0"
PKG_NAME="theme-hub_${PKG_VERSION}_all.deb"

echo "=========================================="
echo " Building Theme Hub Debian Package v${PKG_VERSION}"
echo "=========================================="

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/python3/dist-packages/theme_hub"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/metainfo"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/64x64/apps"
mkdir -p "$BUILD_DIR/usr/share/theme-hub"
mkdir -p "$DIST_DIR"

# 1. Debian metadata
cp "$SCRIPT_DIR/debian/control" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/postinst" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/postrm" "$BUILD_DIR/DEBIAN/"
chmod 755 "$BUILD_DIR/DEBIAN/postinst" "$BUILD_DIR/DEBIAN/postrm"

# 2. Executables
cp "$SCRIPT_DIR/src/bin/theme-hub" "$BUILD_DIR/usr/bin/"
cp "$SCRIPT_DIR/src/bin/theme-hub-cli" "$BUILD_DIR/usr/bin/"
chmod 755 "$BUILD_DIR/usr/bin/"*

# 3. Python package
cp -r "$SCRIPT_DIR/src/theme_hub/"* "$BUILD_DIR/usr/lib/python3/dist-packages/theme_hub/"
find "$BUILD_DIR/usr/lib/python3/dist-packages/theme_hub" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR/usr/lib/python3/dist-packages/theme_hub" -type f -name "*.pyc" -delete 2>/dev/null || true

# 4. Desktop entry & AppStream
cp "$SCRIPT_DIR/data/io.github.themehub.desktop" "$BUILD_DIR/usr/share/applications/"
cp "$SCRIPT_DIR/data/io.github.themehub.metainfo.xml" "$BUILD_DIR/usr/share/metainfo/"
[ -f "$SCRIPT_DIR/data/launchpad.desktop" ] && cp "$SCRIPT_DIR/data/launchpad.desktop" "$BUILD_DIR/usr/share/applications/"

# 5. Icons
cp "$SCRIPT_DIR/assets/branding/io.github.themehub.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/"
cp "$SCRIPT_DIR/assets/branding/io.github.themehub.png" "$BUILD_DIR/usr/share/icons/hicolor/128x128/apps/"
cp "$SCRIPT_DIR/assets/branding/io.github.themehub-64.png" "$BUILD_DIR/usr/share/icons/hicolor/64x64/apps/"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/macos-launchpad.svg" ] && cp "$SCRIPT_DIR/assets/icons/custom-launchers/macos-launchpad.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/macos-launchpad.svg"
[ -f "$SCRIPT_DIR/assets/icons/custom-launchers/windows11-start.svg" ] && cp "$SCRIPT_DIR/assets/icons/custom-launchers/windows11-start.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/windows11-start.svg"

# 6. Bundled Assets (Wallpapers, Cursors, Fonts, Icons, Branding, Plasma Styles)
cp -r "$SCRIPT_DIR/assets/backgrounds" "$BUILD_DIR/usr/share/theme-hub/"
cp -r "$SCRIPT_DIR/assets/cursors" "$BUILD_DIR/usr/share/theme-hub/"
cp -r "$SCRIPT_DIR/assets/fonts" "$BUILD_DIR/usr/share/theme-hub/"
cp -r "$SCRIPT_DIR/assets/icons" "$BUILD_DIR/usr/share/theme-hub/"
cp -r "$SCRIPT_DIR/assets/branding" "$BUILD_DIR/usr/share/theme-hub/"
[ -d "$SCRIPT_DIR/assets/plasma" ] && cp -r "$SCRIPT_DIR/assets/plasma" "$BUILD_DIR/usr/share/theme-hub/"

# 7. Build .deb package
echo "Creating package with dpkg-deb..."
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$DIST_DIR/$PKG_NAME"

# 8. Checksum
sha256sum "$DIST_DIR/$PKG_NAME" > "$DIST_DIR/${PKG_NAME}.sha256"

echo ""
echo "✓ Successfully built: $DIST_DIR/$PKG_NAME"
echo "  SHA-256: $(cat "$DIST_DIR/${PKG_NAME}.sha256" | awk '{print $1}')"
echo "  Size: $(du -h "$DIST_DIR/$PKG_NAME" | awk '{print $1}')"
