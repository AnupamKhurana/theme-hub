"""Unified Desktop Environment Backend for Theme Hub.
Supports GNOME Shell and KDE Plasma 6 with live updates and reliable revert safety.
"""

import os
import shutil
import subprocess
from theme_hub.config import (
    CURRENT_THEME_FILE,
    BACKUP_DIR_GNOME,
    BACKUP_DIR_KDE,
    THEMES,
    get_asset_path,
)


def detect_desktop_environment() -> str:
    """Detect current Desktop Environment (gnome, kde, or generic)."""
    current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()

    if "gnome" in current_desktop or "gnome" in desktop_session:
        return "gnome"
    elif "kde" in current_desktop or "plasma" in desktop_session or os.environ.get("KDE_FULL_SESSION") == "true":
        return "kde"

    # Fallback to checking running processes
    try:
        ps_out = subprocess.check_output(["ps", "-u", str(os.getuid()), "-o", "comm"], text=True)
        if "gnome-shell" in ps_out:
            return "gnome"
        elif "plasmashell" in ps_out or "kwin_wayland" in ps_out:
            return "kde"
    except Exception:
        pass

    return "generic"


def detect_display_server() -> str:
    """Detect Wayland vs X11."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if "wayland" in session_type or "WAYLAND_DISPLAY" in os.environ:
        return "Wayland"
    return "X11"


def get_current_theme() -> str:
    """Get the currently active theme ID."""
    if os.path.exists(CURRENT_THEME_FILE):
        try:
            with open(CURRENT_THEME_FILE, "r") as f:
                t = f.read().strip()
                if t in [th["id"] for th in THEMES]:
                    return t
        except Exception:
            pass

    # Inspect current system settings as fallback
    de = detect_desktop_environment()
    if de == "gnome":
        try:
            out = subprocess.check_output(
                ["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"],
                text=True
            ).strip()
            if "Win11" in out:
                return "windows"
            elif "WhiteSur" in out:
                return "mac"
            elif "Tela" in out:
                return "aesthetic"
            else:
                return "original"
        except Exception:
            return "aesthetic"
    elif de == "kde":
        try:
            out = subprocess.check_output(
                ["kreadconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme"],
                text=True
            ).strip()
            if "Win11" in out:
                return "windows"
            elif "WhiteSur" in out:
                return "mac"
            elif "Tela" in out:
                return "aesthetic"
            else:
                return "original"
        except Exception:
            return "aesthetic"

    return "aesthetic"


def ensure_backup():
    """Ensure baseline configurations are backed up prior to modifications."""
    de = detect_desktop_environment()
    if de == "gnome":
        os.makedirs(BACKUP_DIR_GNOME, exist_ok=True)
        backup_file = os.path.join(BACKUP_DIR_GNOME, "dconf-full-backup.ini")
        if not os.path.exists(backup_file):
            try:
                with open(backup_file, "w") as f:
                    subprocess.run(["dconf", "dump", "/"], stdout=f, check=True)
            except Exception as e:
                print(f"[ThemeHub] Warning: Failed to backup dconf: {e}")

        ghostty_cfg = os.path.expanduser("~/.config/ghostty/config.ghostty")
        ghostty_bak = os.path.join(BACKUP_DIR_GNOME, "config.ghostty.orig")
        if os.path.exists(ghostty_cfg) and not os.path.exists(ghostty_bak):
            shutil.copy2(ghostty_cfg, ghostty_bak)

    elif de == "kde":
        os.makedirs(BACKUP_DIR_KDE, exist_ok=True)
        kde_configs = ["kdeglobals", "kwinrc", "kcminputrc", "plasma-org.kde.plasma.desktop-appletsrc"]
        cfg_home = os.path.expanduser("~/.config")
        for cfg in kde_configs:
            src = os.path.join(cfg_home, cfg)
            dst = os.path.join(BACKUP_DIR_KDE, cfg)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)


def sync_gtk_settings(dark_mode: bool, icon_theme: str, cursor_theme: str, button_layout: str = None):
    """Sync GTK 3 & 4 settings files so cross-toolkit apps (Chrome, Ghostty, etc.) inherit them."""
    gtk_configs = [
        os.path.expanduser("~/.config/gtk-3.0/settings.ini"),
        os.path.expanduser("~/.config/gtk-4.0/settings.ini"),
    ]
    theme_name = "Breeze-Dark" if dark_mode else "Breeze"
    theme_entry = f"""[Settings]
gtk-theme-name={theme_name}
gtk-icon-theme-name={icon_theme}
gtk-cursor-theme-name={cursor_theme}
gtk-application-prefer-dark-theme={'1' if dark_mode else '0'}
"""
    if button_layout:
        theme_entry += f"gtk-decoration-layout={button_layout}\n"

    for path in gtk_configs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w") as f:
                f.write(theme_entry)
        except Exception:
            pass


def apply_theme(theme_id: str) -> bool:
    """Unified entry point to apply a theme or revert."""
    ensure_backup()
    de = detect_desktop_environment()

    if theme_id == "original":
        if de == "gnome":
            success = _revert_gnome()
        elif de == "kde":
            success = _revert_kde()
        else:
            success = _revert_generic()
    else:
        if de == "gnome":
            success = _apply_gnome(theme_id)
        elif de == "kde":
            success = _apply_kde(theme_id)
        else:
            success = _apply_generic(theme_id)

    if success:
        os.makedirs(os.path.dirname(CURRENT_THEME_FILE), exist_ok=True)
        with open(CURRENT_THEME_FILE, "w") as f:
            f.write(theme_id + "\n")

        theme_title = next((t["title"] for t in THEMES if t["id"] == theme_id), theme_id)
        notify_user("Theme Changed", f"Successfully activated {theme_title}")

    return success


def _apply_gnome(theme_id: str) -> bool:
    """Apply theme settings for GNOME Shell."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    # 1. Dark mode & Themes
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "accent-color", theme.get("accent_name", "blue")])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Adwaita-dark"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme["icon_theme"]])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme["cursor_theme"]])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-size", "24"])

    # 2. Typography
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "font-name", "Inter 10.5"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "document-font-name", "Inter 10.5"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "monospace-font-name", "JetBrains Mono 10.5"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "titlebar-font", "Inter Semi-Bold 10.5"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "font-antialiasing", "rgba"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "font-hinting", "slight"])

    # 3. Window Button Layout
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", theme["button_layout_gnome"]])

    # 4. Wallpaper
    if "wallpaper" in theme:
        wall_path = get_asset_path(*theme["wallpaper"])
        subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{wall_path}"])
        subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{wall_path}"])
    elif "wallpaper_dark" in theme:
        wall_d = get_asset_path(*theme["wallpaper_dark"])
        wall_l = get_asset_path(*theme.get("wallpaper_light", theme["wallpaper_dark"]))
        subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{wall_l}"])
        subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{wall_d}"])

    # 5. Dash to Panel configurations
    _apply_dash_to_panel_gnome(theme_id)

    # 6. Terminal theming (Ghostty)
    _apply_ghostty_theme(theme_id)

    return True


def _apply_dash_to_panel_gnome(theme_id: str):
    """Configure Dash-to-Panel extension for GNOME Shell."""
    launchpad_icon = get_asset_path("icons", "custom-launchers", "macos-launchpad.svg")

    if theme_id == "aesthetic":
        d = {
            'stockgs-keep-top-panel': 'false',
            'panel-lengths': '{"AUO-0x00000000":100}',
            'panel-sizes': '{"AUO-0x00000000":44}',
            'panel-positions': '{"AUO-0x00000000":"BOTTOM"}',
            'panel-anchors': '{"AUO-0x00000000":"MIDDLE"}',
            'panel-top-bottom-margins': '6',
            'panel-side-margins': '12',
            'global-border-radius': '12',
            'trans-use-custom-opacity': 'true',
            'trans-panel-opacity': '0.85',
            'trans-use-custom-bg': 'true',
            'trans-bg-color': '#11141c',
            'dot-style-focused': 'DOTS',
            'dot-style-unfocused': 'DOTS',
            'dot-color-dominant': 'true',
            'dot-color-override': 'false',
            'highlight-appicon-hover': 'true',
            'highlight-appicon-hover-border-radius': '8',
            'animate-appicon-hover': 'true',
            'animate-appicon-hover-animation-type': 'RIPPLE',
            'show-apps-icon-file': '',
            'panel-element-positions': '{"AUO-0x00000000":[{"element":"showAppsButton","visible":true,"position":"stackedTL"},{"element":"leftBox","visible":true,"position":"stackedTL"},{"element":"taskbar","visible":true,"position":"centerMonitor"},{"element":"activitiesButton","visible":false,"position":"stackedBR"},{"element":"centerBox","visible":true,"position":"stackedBR"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"dateMenu","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":false,"position":"stackedBR"}]}'
        }
    elif theme_id == "windows":
        d = {
            'stockgs-keep-top-panel': 'false',
            'panel-lengths': '{"AUO-0x00000000":100}',
            'panel-sizes': '{"AUO-0x00000000":48}',
            'panel-positions': '{"AUO-0x00000000":"BOTTOM"}',
            'panel-anchors': '{"AUO-0x00000000":"MIDDLE"}',
            'panel-top-bottom-margins': '0',
            'panel-side-margins': '0',
            'global-border-radius': '0',
            'trans-use-custom-opacity': 'true',
            'trans-panel-opacity': '0.88',
            'trans-use-custom-bg': 'true',
            'trans-bg-color': '#1c1c1c',
            'dot-style-focused': 'METRO',
            'dot-style-unfocused': 'METRO',
            'dot-size': '3',
            'dot-position': 'BOTTOM',
            'dot-color-dominant': 'false',
            'dot-color-override': 'true',
            'dot-color-unfocused-different': 'false',
            'custom-color-dots': '#0078d4',
            'highlight-appicon-hover': 'true',
            'highlight-appicon-hover-border-radius': '4',
            'animate-appicon-hover': 'true',
            'animate-appicon-hover-animation-type': 'SIMPLE',
            'show-apps-icon-file': '',
            'panel-element-positions': '{"AUO-0x00000000":[{"element":"showAppsButton","visible":true,"position":"centerMonitor"},{"element":"taskbar","visible":true,"position":"centerMonitor"},{"element":"leftBox","visible":false,"position":"stackedTL"},{"element":"activitiesButton","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":true,"position":"stackedBR"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"dateMenu","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":true,"position":"stackedBR"}]}'
        }
    elif theme_id == "mac":
        d = {
            'stockgs-keep-top-panel': 'true',
            'panel-lengths': '{"AUO-0x00000000":-1}',
            'panel-sizes': '{"AUO-0x00000000":54}',
            'panel-positions': '{"AUO-0x00000000":"BOTTOM"}',
            'panel-anchors': '{"AUO-0x00000000":"MIDDLE"}',
            'panel-top-bottom-margins': '10',
            'panel-side-margins': '0',
            'global-border-radius': '18',
            'trans-use-custom-opacity': 'true',
            'trans-panel-opacity': '0.60',
            'trans-use-custom-bg': 'true',
            'trans-bg-color': '#1e1e1e',
            'dot-style-focused': 'DOTS',
            'dot-style-unfocused': 'DOTS',
            'dot-size': '4',
            'dot-position': 'BOTTOM',
            'dot-color-dominant': 'false',
            'dot-color-override': 'false',
            'highlight-appicon-hover': 'true',
            'highlight-appicon-hover-border-radius': '10',
            'animate-appicon-hover': 'true',
            'animate-appicon-hover-animation-type': 'PLANK',
            'show-apps-icon-file': launchpad_icon if os.path.exists(launchpad_icon) else '',
            'panel-element-positions': '{"AUO-0x00000000":[{"element":"showAppsButton","visible":true,"position":"stackedTL"},{"element":"taskbar","visible":true,"position":"stackedTL"},{"element":"leftBox","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":false,"position":"centered"},{"element":"activitiesButton","visible":false,"position":"stackedBR"},{"element":"rightBox","visible":false,"position":"stackedBR"},{"element":"dateMenu","visible":false,"position":"stackedBR"},{"element":"systemMenu","visible":false,"position":"stackedBR"},{"element":"desktopButton","visible":false,"position":"stackedBR"}]}'
        }
    else:
        return

    for k, v in d.items():
        val = f"'{v}'" if not v.isdigit() and v not in ['true', 'false'] else v
        subprocess.call(['dconf', 'write', f'/org/gnome/shell/extensions/dash-to-panel/{k}', val])


def _apply_ghostty_theme(theme_id: str):
    """Configure Ghostty terminal aesthetic matching."""
    ghostty_dir = os.path.expanduser("~/.config/ghostty")
    cfg_file = os.path.join(ghostty_dir, "config.ghostty")
    if not os.path.exists(cfg_file) and not os.path.exists(ghostty_dir):
        return

    os.makedirs(ghostty_dir, exist_ok=True)
    cfg_content = """theme = Catppuccin Mocha
font-family = JetBrains Mono
font-size = 11.5
cursor-style = bar
cursor-style-blink = true
background-opacity = 0.92
background-blur-radius = 20
window-padding-x = 12
window-padding-y = 10
window-padding-balance = true
window-decoration = auto
gtk-titlebar = true
"""
    try:
        with open(cfg_file, "w") as f:
            f.write(cfg_content)
    except Exception:
        pass


def _apply_kde(theme_id: str) -> bool:
    """Apply theme settings for KDE Plasma 6 cleanly without killing plasmashell."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    # 1. Colorscheme & Accent
    subprocess.call(["plasma-apply-colorscheme", "BreezeDark", "-a", theme["color"]])
    subprocess.call(["plasma-apply-desktoptheme", "breeze-dark"])

    # 2. Icons & Cursors
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", theme["icon_theme"]])
    subprocess.call(["plasma-apply-cursortheme", theme["cursor_theme"]])

    # 3. Typography
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "font", "Inter,10.5,-1,5,50,0,0,0,0,0"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "fixed", "JetBrains Mono,10.5,-1,5,50,0,0,0,0,0"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "WM", "--key", "activeFont", "Inter Semi-Bold,10.5,-1,5,75,0,0,0,0,0"])

    # 4. Window Buttons
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnLeft", theme["button_layout_kde_left"]])
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnRight", theme["button_layout_kde_right"]])

    # 5. Wallpaper
    if "wallpaper" in theme:
        wall_path = get_asset_path(*theme["wallpaper"])
    else:
        wall_path = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))
    subprocess.call(["plasma-apply-wallpaperimage", wall_path])

    # 6. Sync GSettings & GTK 3/4 settings for GTK apps running on KDE
    gtk_layout = "close,minimize,maximize:appmenu" if theme_id == "mac" else "appmenu:minimize,maximize,close"
    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"], button_layout=gtk_layout)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme["icon_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme["cursor_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", gtk_layout], stderr=subprocess.DEVNULL)

    # 7. Live KWin & Sycoca reload
    subprocess.call(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], stderr=subprocess.DEVNULL)
    subprocess.call(["kbuildsycoca6", "--noincremental"], stderr=subprocess.DEVNULL)

    return True


def _apply_generic(theme_id: str) -> bool:
    """Fallback theme application for generic desktop environments."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"])
    if "wallpaper" in theme:
        wall = get_asset_path(*theme["wallpaper"])
    else:
        wall = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))

    # Try setting wallpaper via feh or nitrogen if present
    subprocess.call(["feh", "--bg-fill", wall], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme["icon_theme"]], stderr=subprocess.DEVNULL)
    return True


def _revert_gnome() -> bool:
    """Revert GNOME Shell to original stock settings."""
    # 1. Interface defaults
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Adwaita"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Adwaita"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "default"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", "Adwaita"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "font-name", "Cantarell 11"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "document-font-name", "Cantarell 11"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "monospace-font-name", "Monospace 11"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "titlebar-font", "Adwaita Sans Bold 11"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "accent-color", "orange"])
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", "appmenu:close"])

    # Stock wallpapers
    for wall in ["/usr/share/backgrounds/gnome/pride-l.jxl", "/usr/share/backgrounds/gnome/adwaita-l.webp"]:
        if os.path.exists(wall):
            subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{wall}"])
            break

    # 2. Restore full dconf dump if available
    backup_file = os.path.join(BACKUP_DIR_GNOME, "dconf-full-backup.ini")
    if os.path.exists(backup_file):
        try:
            with open(backup_file, "r") as f:
                subprocess.run(["dconf", "load", "/"], stdin=f, check=True)
        except Exception:
            pass

    # 3. Restore ghostty
    ghostty_bak = os.path.join(BACKUP_DIR_GNOME, "config.ghostty.orig")
    ghostty_cfg = os.path.expanduser("~/.config/ghostty/config.ghostty")
    if os.path.exists(ghostty_bak):
        shutil.copy2(ghostty_bak, ghostty_cfg)

    return True


def _revert_kde() -> bool:
    """Revert KDE Plasma to original stock settings without crashing."""
    subprocess.call(["plasma-apply-colorscheme", "BreezeLight"], stderr=subprocess.DEVNULL)
    subprocess.call(["plasma-apply-desktoptheme", "breeze-light"], stderr=subprocess.DEVNULL)
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", "breeze"])
    subprocess.call(["plasma-apply-cursortheme", "breeze_cursors"], stderr=subprocess.DEVNULL)
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnLeft", "M"])
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnRight", "IAX"])

    # Restore default Debian wallpaper
    for deb_wall in ["/usr/share/wallpapers/DebianTheme", "/usr/share/wallpapers/Next"]:
        if os.path.exists(deb_wall):
            subprocess.call(["plasma-apply-wallpaperimage", deb_wall], stderr=subprocess.DEVNULL)
            break

    # Restore GTK
    sync_gtk_settings(dark_mode=False, icon_theme="breeze", cursor_theme="breeze_cursors")

    # Reload KWin
    subprocess.call(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], stderr=subprocess.DEVNULL)
    subprocess.call(["kbuildsycoca6", "--noincremental"], stderr=subprocess.DEVNULL)
    return True


def _revert_generic() -> bool:
    """Revert generic environment."""
    sync_gtk_settings(dark_mode=False, icon_theme="Adwaita", cursor_theme="Adwaita")
    return True


def notify_user(title: str, message: str):
    """Deliver a native desktop notification."""
    icon_path = get_asset_path("branding", "io.github.themehub.png")
    icon_arg = f"--icon={icon_path}" if os.path.exists(icon_path) else "--icon=preferences-desktop-theme"
    subprocess.call(["notify-send", title, message, icon_arg], stderr=subprocess.DEVNULL)
