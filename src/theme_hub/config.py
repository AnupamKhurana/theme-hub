"""Configuration and theme definitions for Theme Hub."""
import os
import sys

APP_ID = "io.github.themehub"
APP_NAME = "Theme Hub"
APP_VERSION = "1.0.0"

# Directories
CURRENT_THEME_FILE = os.path.expanduser("~/.config/ui-current-theme")
BACKUP_DIR_GNOME = os.path.expanduser("~/.config/ui-aesthetic-backup")
BACKUP_DIR_KDE = os.path.expanduser("~/.config/ui-aesthetic-backup/kde-backup")

def resolve_asset_dir():
    """Find the root directory where theme-hub assets are installed or located."""
    candidates = [
        # System installation path
        "/usr/share/theme-hub",
        "/usr/local/share/theme-hub",
        # User local installation path
        os.path.expanduser("~/.local/share/theme-hub"),
        # Source tree during development
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets")),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    # Fallback to current working directory assets if present
    if os.path.isdir("assets"):
        return os.path.abspath("assets")
    return "/usr/share/theme-hub"

ASSET_DIR = resolve_asset_dir()

def get_asset_path(*parts):
    """Resolve a specific asset file path."""
    primary = os.path.join(ASSET_DIR, *parts)
    if os.path.exists(primary):
        return primary
    
    # Check legacy user home locations (~/.local/share/backgrounds/...)
    if parts[0] == "backgrounds" and len(parts) >= 3:
        legacy = os.path.expanduser(f"~/.local/share/backgrounds/{parts[1]}/{parts[2]}")
        if os.path.exists(legacy):
            return legacy
    elif parts[0] == "icons" and len(parts) >= 2:
        legacy = os.path.expanduser(f"~/.local/share/icons/{'/'.join(parts[1:])}")
        if os.path.exists(legacy):
            return legacy

    return primary

THEMES = [
    {
        "id": "aesthetic",
        "title": "Modern Aesthetic",
        "subtitle": "Dark minimalist aesthetic • Tela Circle icons • Floating centered dock • Calm Night wallpaper",
        "icon": "/usr/share/icons/hicolor/scalable/apps/io.github.themehub.svg",
        "color": "#3584e4",
        "accent_name": "blue",
        "wallpaper": ("backgrounds", "aesthetic", "calm-night.png"),
        "icon_theme": "Tela-circle-dark",
        "cursor_theme": "Bibata-Modern-Classic",
        "font_family": "Inter",
        "font_mono": "JetBrains Mono",
        "button_layout_gnome": "appmenu:close",
        "button_layout_kde_left": "",
        "button_layout_kde_right": "X",
        "description": "Clean, focused, modern dark theme designed for distraction-free coding and daily computing."
    },
    {
        "id": "windows",
        "title": "Windows 11 Look",
        "subtitle": "Fluent icons • Bloom 4K wallpaper • Right titlebar controls (:min,max,close) • Centered taskbar",
        "icon": "/usr/share/icons/custom-launchers/windows11-start.svg",
        "color": "#0078d4",
        "accent_name": "blue",
        "wallpaper_dark": ("backgrounds", "windows", "bloom-dark.jpg"),
        "wallpaper_light": ("backgrounds", "windows", "bloom-light.jpg"),
        "icon_theme": "Win11-dark",
        "cursor_theme": "Bibata-Modern-Classic",
        "font_family": "Inter",
        "font_mono": "JetBrains Mono",
        "button_layout_gnome": "appmenu:minimize,maximize,close",
        "button_layout_kde_left": "M",
        "button_layout_kde_right": "IAX",
        "description": "Authentic Windows 11 Fluent aesthetic featuring Bloom wallpaper, soft rounded borders, and right-aligned window controls."
    },
    {
        "id": "mac",
        "title": "macOS Sonoma Look",
        "subtitle": "WhiteSur icons • Sonoma 4K wallpaper • Left traffic lights (close,min,max:) • Top menu + Floating dock",
        "icon": "/usr/share/icons/custom-launchers/macos-launchpad.svg",
        "color": "#e5a50a",
        "accent_name": "orange",
        "wallpaper_dark": ("backgrounds", "mac", "sonoma-dark.jpg"),
        "wallpaper_light": ("backgrounds", "mac", "sonoma-light.jpg"),
        "icon_theme": "WhiteSur-dark",
        "cursor_theme": "macOS",
        "font_family": "Inter",
        "font_mono": "JetBrains Mono",
        "button_layout_gnome": "close,minimize,maximize:appmenu",
        "button_layout_kde_left": "XIA",
        "button_layout_kde_right": "",
        "description": "Elegant Apple macOS design language featuring vibrant Sonoma wallpaper, left traffic-light buttons, and floating glass dock."
    },
    {
        "id": "original",
        "title": "Stock Linux Defaults",
        "subtitle": "Restore default system themes, stock wallpapers, standard titlebar buttons, and original desktop layout",
        "icon": "edit-undo-symbolic",
        "color": "#e01b24",
        "accent_name": "default",
        "wallpaper": None,
        "icon_theme": "Adwaita",
        "cursor_theme": "Adwaita",
        "font_family": "Cantarell",
        "font_mono": "Monospace",
        "button_layout_gnome": "appmenu:close",
        "button_layout_kde_left": "M",
        "button_layout_kde_right": "IAX",
        "description": "Restores your desktop to the original factory default configuration without losing any personal files or applications."
    }
]
