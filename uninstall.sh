#!/usr/bin/env bash
set -e

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
            echo "Theme Hub Uninstaller"
            echo "Usage: ./uninstall.sh [--user | --system]"
            exit 0
            ;;
    esac
done

if [ "$MODE" = "system" ] && [ "$(id -u)" -ne 0 ]; then
    echo "Warning: System-wide uninstallation requires root privileges."
    echo "Rerunning with sudo..."
    exec sudo "$0" --system
fi

echo "Uninstalling Theme Hub ($MODE mode)..."

if [ "$MODE" = "system" ]; then
    rm -f /usr/local/bin/theme-hub /usr/local/bin/theme-hub-cli
    rm -rf /usr/local/lib/python3/dist-packages/theme_hub
    rm -rf /usr/local/share/theme-hub
    rm -f /usr/share/applications/io.github.themehub.desktop
    rm -f /usr/share/icons/hicolor/*/apps/io.github.themehub*
    rm -rf /usr/share/fonts/truetype/theme-hub
else
    rm -f "$HOME/.local/bin/theme-hub" "$HOME/.local/bin/theme-hub-cli"
    rm -rf "$HOME/.local/lib/python3/dist-packages/theme_hub"
    rm -rf "$HOME/.local/share/theme-hub"
    rm -f "$HOME/.local/share/applications/io.github.themehub.desktop"
    rm -f "$HOME/.local/share/icons/hicolor/*/apps/io.github.themehub*"
fi

echo "Refreshing caches..."
which update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
which fc-cache >/dev/null 2>&1 && fc-cache -f || true

echo "✓ Theme Hub successfully uninstalled."
