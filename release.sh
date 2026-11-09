#!/usr/bin/env bash
# ==============================================================================
# Theme Hub Release Script
# Builds package, creates git tag, and publishes GitHub Release via gh CLI.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="${1:-1.0.0}"
TAG="v${VERSION#v}"
TITLE="Theme Hub ${TAG}"

echo "=========================================="
echo " Preparing GitHub Release: ${TAG}"
echo "=========================================="

# 1. Build .deb package
echo "[1/4] Building Debian package..."
./build.sh

DEB_FILE="dist/theme-hub_${VERSION#v}_all.deb"
SHA_FILE="${DEB_FILE}.sha256"

if [[ ! -f "$DEB_FILE" ]]; then
  echo "Error: Expected build output $DEB_FILE not found!" >&2
  exit 1
fi

# 2. Check git status
echo "[2/4] Checking git repository status..."
if ! git diff-index --quiet HEAD --; then
  echo "Warning: Uncommitted changes detected. Staging and committing..."
  git add -A
  git commit -m "chore(release): prepare ${TAG}"
fi

# 3. Create or update git tag
echo "[3/4] Ensuring git tag ${TAG}..."
if git rev-parse "${TAG}" >/dev/null 2>&1; then
  echo "Tag ${TAG} already exists locally. Updating tag to HEAD..."
  git tag -f "${TAG}"
else
  git tag -a "${TAG}" -m "Release ${TAG}"
fi

# Push commit & tag to origin if remote exists
if git remote get-url origin >/dev/null 2>&1; then
  echo "Pushing commits and tags to origin..."
  git push origin HEAD
  git push origin "${TAG}" --force
fi

# 4. Create GitHub Release with gh CLI
echo "[4/4] Creating GitHub Release via gh CLI..."
RELEASE_NOTES="### Theme Hub ${TAG}

Handcrafted desktop appearance studio and theme switcher for Linux (GNOME & KDE Plasma 6).

#### Highlights in this release:
- 🍎 **macOS Sonoma Look**: Authentic centered glass dock, dodge windows, top menu bar with Apple menu & Launchpad, full WhiteSur-dark plasma theme, and custom squircle icons (TradingView, YouTube, EquityAI, Antigravity).
- 🎨 **Modern Aesthetic**: Dark minimalist look with Inter typography, Tela Circle icons, floating dock, and Calm Night 4K wallpaper.
- 🔄 **Original Stock Defaults**: Safe, one-click restoration to default system settings.
- 🐧 **Full KDE Plasma 6 & GNOME Support**: Native DBus and configuration integration across Wayland and X11.

#### Installation:
\`\`\`bash
# Download and install via apt
sudo apt install ./theme-hub_${VERSION#v}_all.deb
\`\`\`"

if gh release view "${TAG}" >/dev/null 2>&1; then
  echo "Updating existing release ${TAG}..."
  gh release upload "${TAG}" "$DEB_FILE" "$SHA_FILE" --clobber
else
  gh release create "${TAG}" "$DEB_FILE" "$SHA_FILE" \
    --title "$TITLE" \
    --notes "$RELEASE_NOTES"
fi

echo "=========================================="
echo "✓ Release ${TAG} published successfully!"
echo "  URL: $(gh release view "${TAG}" --json url -q .url)"
echo "=========================================="
