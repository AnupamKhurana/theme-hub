"""Unified Desktop Environment Backend for Theme Hub.
Supports GNOME Shell and KDE Plasma 6 with live updates and reliable revert safety.
"""

import os
import shutil
import subprocess
import time
from theme_hub.config import (
    CURRENT_THEME_FILE,
    BACKUP_DIR_GNOME,
    BACKUP_DIR_KDE,
    BACKUP_DIR_CINNAMON,
    BACKUP_DIR_XFCE,
    BACKUP_DIR_MATE,
    THEMES,
    get_asset_path,
)


def _setup_env():
    """Ensure XDG and Wayland / X11 environment variables are set."""
    uid = os.getuid()
    if "XDG_RUNTIME_DIR" not in os.environ:
        os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"

    runtime_dir = os.environ["XDG_RUNTIME_DIR"]
    if "WAYLAND_DISPLAY" not in os.environ and os.path.exists(runtime_dir):
        for f in os.listdir(runtime_dir):
            if f.startswith("wayland-"):
                os.environ["WAYLAND_DISPLAY"] = f
                break

    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":1"

    if "XAUTHORITY" not in os.environ and os.path.exists(runtime_dir):
        for f in os.listdir(runtime_dir):
            if f.startswith("xauth_"):
                os.environ["XAUTHORITY"] = os.path.join(runtime_dir, f)
                break


def detect_desktop_environment() -> str:
    """Detect current Desktop Environment (gnome, kde, cinnamon, xfce, mate, or generic)."""
    current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()

    if "cinnamon" in current_desktop or "cinnamon" in desktop_session or "x-cinnamon" in desktop_session:
        return "cinnamon"
    elif "xfce" in current_desktop or "xfce" in desktop_session or "xubuntu" in desktop_session:
        return "xfce"
    elif "mate" in current_desktop or "mate" in desktop_session:
        return "mate"
    elif "gnome" in current_desktop or "gnome" in desktop_session or "ubuntu" in current_desktop:
        return "gnome"
    elif "kde" in current_desktop or "plasma" in desktop_session or os.environ.get("KDE_FULL_SESSION") == "true":
        return "kde"

    # Fallback to checking running processes
    try:
        ps_out = subprocess.check_output(["ps", "-u", str(os.getuid()), "-o", "comm"], text=True)
        if "cinnamon" in ps_out:
            return "cinnamon"
        elif "xfce4-session" in ps_out or "xfwm4" in ps_out:
            return "xfce"
        elif "mate-session" in ps_out:
            return "mate"
        elif "gnome-shell" in ps_out:
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
    if de in ["gnome", "cinnamon", "mate"]:
        schema = "org.gnome.desktop.interface" if de == "gnome" else ("org.cinnamon.desktop.interface" if de == "cinnamon" else "org.mate.interface")
        try:
            out = subprocess.check_output(
                ["gsettings", "get", schema, "icon-theme"],
                text=True
            ).strip()
            if "WhiteSur" in out:
                return "mac"
            elif "Win11" in out:
                return "windows"
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
            if "WhiteSur" in out:
                return "mac"
            elif "Win11" in out:
                return "windows"
            elif "Tela" in out:
                return "aesthetic"
            else:
                return "original"
        except Exception:
            return "aesthetic"
    elif de == "xfce":
        try:
            out = subprocess.check_output(
                ["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName"],
                text=True
            ).strip()
            if "WhiteSur" in out:
                return "mac"
            elif "Win11" in out:
                return "windows"
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
        kde_configs = ["kdeglobals", "kwinrc", "kcminputrc", "plasma-org.kde.plasma.desktop-appletsrc", "plasmarc"]
        cfg_home = os.path.expanduser("~/.config")
        for cfg in kde_configs:
            src = os.path.join(cfg_home, cfg)
            dst = os.path.join(BACKUP_DIR_KDE, cfg)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)

    elif de == "cinnamon":
        os.makedirs(BACKUP_DIR_CINNAMON, exist_ok=True)
        backup_file = os.path.join(BACKUP_DIR_CINNAMON, "cinnamon-backup.dconf")
        if not os.path.exists(backup_file):
            try:
                with open(backup_file, "w") as f:
                    subprocess.run(["dconf", "dump", "/org/cinnamon/"], stdout=f, check=True)
            except Exception:
                pass

    elif de == "mate":
        os.makedirs(BACKUP_DIR_MATE, exist_ok=True)
        backup_file = os.path.join(BACKUP_DIR_MATE, "mate-backup.dconf")
        if not os.path.exists(backup_file):
            try:
                with open(backup_file, "w") as f:
                    subprocess.run(["dconf", "dump", "/org/mate/"], stdout=f, check=True)
            except Exception:
                pass


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
        elif de == "cinnamon":
            success = _revert_cinnamon()
        elif de == "xfce":
            success = _revert_xfce()
        elif de == "mate":
            success = _revert_mate()
        else:
            success = _revert_generic()
    else:
        if de == "gnome":
            success = _apply_gnome(theme_id)
        elif de == "kde":
            success = _apply_kde(theme_id)
        elif de == "cinnamon":
            success = _apply_cinnamon(theme_id)
        elif de == "xfce":
            success = _apply_xfce(theme_id)
        elif de == "mate":
            success = _apply_mate(theme_id)
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

    if theme_id == "mac":
        ensure_whitesur_icons()
    elif theme_id == "windows":
        ensure_win11_icons()
        ensure_windows_start_icon()
    elif theme_id == "aesthetic":
        ensure_tela_icons()
        ensure_modern_start_icon()

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
    elif theme_id == "windows":
        win_start_icon = get_asset_path("icons", "custom-launchers", "windows11-start.svg")
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
            'trans-panel-opacity': '0.90',
            'trans-use-custom-bg': 'true',
            'trans-bg-color': '#1c1c1c',
            'dot-style-focused': 'METRO',
            'dot-style-unfocused': 'NONE',
            'dot-size': '3',
            'dot-position': 'BOTTOM',
            'dot-color-dominant': 'false',
            'dot-color-override': 'false',
            'highlight-appicon-hover': 'true',
            'highlight-appicon-hover-border-radius': '4',
            'animate-appicon-hover': 'true',
            'animate-appicon-hover-animation-type': 'SIMPLE',
            'show-apps-icon-file': win_start_icon if os.path.exists(win_start_icon) else '',
            'panel-element-positions': '{"AUO-0x00000000":[{"element":"showAppsButton","visible":true,"position":"centerMonitor"},{"element":"taskbar","visible":true,"position":"centerMonitor"},{"element":"leftBox","visible":false,"position":"stackedTL"},{"element":"centerBox","visible":false,"position":"centered"},{"element":"activitiesButton","visible":false,"position":"stackedBR"},{"element":"rightBox","visible":true,"position":"stackedBR"},{"element":"systemMenu","visible":true,"position":"stackedBR"},{"element":"dateMenu","visible":true,"position":"stackedBR"},{"element":"desktopButton","visible":false,"position":"stackedBR"}]}'
        }
    else:
        return

    for k, v in d.items():
        val = f"'{v}'" if not v.isdigit() and v not in ['true', 'false'] else v
        subprocess.call(['dconf', 'write', f'/org/gnome/shell/extensions/dash-to-panel/{k}', val])

    if theme_id == "mac":
        subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "clock-show-date", "true"], stderr=subprocess.DEVNULL)
        subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "clock-show-weekday", "true"], stderr=subprocess.DEVNULL)


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


def _reload_kde_icons():
    """Trigger KDE Frameworks 6 to immediately reload all icon loaders and caches."""
    try:
        import ctypes
        kf6 = ctypes.CDLL("libKF6IconThemes.so.6")
        kf6._ZN11KIconLoader10emitChangeENS_5GroupE(0)
    except Exception:
        pass
    subprocess.call(["dbus-send", "--type=signal", "--session", "/KIconLoader", "org.kde.KIconLoader.iconChanged", "int32:0"], stderr=subprocess.DEVNULL)
    subprocess.call(["kbuildsycoca6", "--noincremental"], stderr=subprocess.DEVNULL)


def ensure_whitesur_icons():
    """Ensure WhiteSur-dark icon theme with all scalable application icons is present and valid."""
    user_icon_theme = os.path.expanduser("~/.local/share/icons/WhiteSur-dark")
    scalable_check = os.path.join(user_icon_theme, "apps", "scalable")
    tv_check = os.path.join(scalable_check, "com.tradingview.tradingview.svg")
    # If scalable dir is missing or is a broken symlink, sync complete bundled icons
    if not os.path.exists(user_icon_theme) or not os.path.isdir(scalable_check) or os.path.islink(scalable_check) or not os.path.exists(tv_check):
        repo_icons = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "WhiteSur-dark"))
        if os.path.exists(repo_icons) and os.path.isdir(os.path.join(repo_icons, "apps", "scalable")) and not os.path.islink(os.path.join(repo_icons, "apps", "scalable")):
            bundled_icons = repo_icons
        else:
            bundled_icons = get_asset_path("icons", "WhiteSur-dark")

        if os.path.exists(bundled_icons):
            os.makedirs(os.path.dirname(user_icon_theme), exist_ok=True)
            if os.path.exists(user_icon_theme):
                if os.path.islink(user_icon_theme):
                    os.unlink(user_icon_theme)
                else:
                    shutil.rmtree(user_icon_theme)
            shutil.copytree(bundled_icons, user_icon_theme, symlinks=True)
            subprocess.call(["gtk-update-icon-cache", "-f", "-t", user_icon_theme], stderr=subprocess.DEVNULL)


def ensure_win11_icons():
    """Ensure Win11-dark icon theme with all scalable application icons is present and valid."""
    user_icon_theme = os.path.expanduser("~/.local/share/icons/Win11-dark")
    scalable_check = os.path.join(user_icon_theme, "apps", "scalable")
    settings_check = os.path.join(scalable_check, "systemsettings.svg")
    if not os.path.exists(user_icon_theme) or not os.path.isdir(scalable_check) or os.path.islink(scalable_check) or not os.path.exists(settings_check) or os.path.islink(settings_check):
        repo_icons = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "Win11-dark"))
        if os.path.exists(repo_icons) and os.path.isdir(os.path.join(repo_icons, "apps", "scalable")) and not os.path.islink(os.path.join(repo_icons, "apps", "scalable")):
            bundled_icons = repo_icons
        else:
            bundled_icons = get_asset_path("icons", "Win11-dark")

        if os.path.exists(bundled_icons):
            os.makedirs(os.path.dirname(user_icon_theme), exist_ok=True)
            if os.path.exists(user_icon_theme):
                if os.path.islink(user_icon_theme):
                    os.unlink(user_icon_theme)
                else:
                    shutil.rmtree(user_icon_theme)
            shutil.copytree(bundled_icons, user_icon_theme, symlinks=True)
            subprocess.call(["gtk-update-icon-cache", "-f", "-t", user_icon_theme], stderr=subprocess.DEVNULL)


def ensure_windows_start_icon():
    """Ensure Windows 11 Start icon is installed in user icon directory."""
    user_icon_dir = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps")
    os.makedirs(user_icon_dir, exist_ok=True)
    dst_icon = os.path.join(user_icon_dir, "windows11-start.svg")
    if not os.path.exists(dst_icon):
        src_icon = get_asset_path("icons", "custom-launchers", "windows11-start.svg")
        if os.path.exists(src_icon):
            shutil.copy2(src_icon, dst_icon)


def ensure_tela_icons():
    """Ensure Tela-circle and Tela-circle-dark icon themes are installed in user icons."""
    for theme_name in ["Tela-circle", "Tela-circle-dark"]:
        user_icon_theme = os.path.expanduser(f"~/.local/share/icons/{theme_name}")
        app_check = os.path.join(user_icon_theme, "scalable", "apps", "systemsettings.svg")
        if not os.path.exists(user_icon_theme) or not os.path.exists(app_check):
            repo_icons = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", theme_name))
            if os.path.exists(repo_icons):
                bundled_icons = repo_icons
            else:
                bundled_icons = get_asset_path("icons", theme_name)

            if os.path.exists(bundled_icons):
                os.makedirs(os.path.dirname(user_icon_theme), exist_ok=True)
                if os.path.exists(user_icon_theme):
                    if os.path.islink(user_icon_theme):
                        os.unlink(user_icon_theme)
                    else:
                        shutil.rmtree(user_icon_theme)
                shutil.copytree(bundled_icons, user_icon_theme, symlinks=True)
                subprocess.call(["gtk-update-icon-cache", "-f", "-t", user_icon_theme], stderr=subprocess.DEVNULL)


def ensure_modern_start_icon():
    """Ensure Modern Aesthetic Start icon is installed in user icon directory."""
    user_icon_dir = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps")
    os.makedirs(user_icon_dir, exist_ok=True)
    dst_icon = os.path.join(user_icon_dir, "modern-start.svg")
    src_icon = get_asset_path("icons", "custom-launchers", "modern-start.svg")
    if not os.path.exists(src_icon):
        repo_icon = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "custom-launchers", "modern-start.svg"))
        if os.path.exists(repo_icon):
            src_icon = repo_icon
    if os.path.exists(src_icon):
        shutil.copy2(src_icon, dst_icon)


def ensure_kde_plasma_theme():
    """Ensure WhiteSur-dark plasma desktop theme is installed in user's plasma directory."""
    user_theme_dir = os.path.expanduser("~/.local/share/plasma/desktoptheme/WhiteSur-dark")
    if not os.path.exists(user_theme_dir):
        bundled_theme = get_asset_path("plasma", "desktoptheme", "WhiteSur-dark")
        if os.path.exists(bundled_theme):
            os.makedirs(os.path.dirname(user_theme_dir), exist_ok=True)
            shutil.copytree(bundled_theme, user_theme_dir)


def ensure_launchpad_desktop():
    """Ensure Launchpad desktop entry and icon are installed for the dock."""
    user_icon_dir = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps")
    os.makedirs(user_icon_dir, exist_ok=True)
    dst_icon = os.path.join(user_icon_dir, "macos-launchpad.svg")
    if not os.path.exists(dst_icon):
        src_icon = get_asset_path("icons", "custom-launchers", "macos-launchpad.svg")
        if os.path.exists(src_icon):
            shutil.copy2(src_icon, dst_icon)

    user_app_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(user_app_dir, exist_ok=True)
    dst_desktop = os.path.join(user_app_dir, "launchpad.desktop")
    if not os.path.exists(dst_desktop):
        content = """[Desktop Entry]
Name=Launchpad
Comment=Open Application Launcher
Exec=qdbus6 org.kde.plasmashell /PlasmaShell activateLauncherMenu
Icon=macos-launchpad
Terminal=false
Type=Application
Categories=System;Utility;
"""
        with open(dst_desktop, "w") as f:
            f.write(content)


def _configure_kde_panel(theme_id: str):
    """Configure authentic panels for KDE Plasma 6:
    - mac: Top Apple Menu Bar (Kickoff + Global AppMenu + Spacer + Tray + Clock) + Floating Centered Glass Dock (Launchpad + IconTasks + Separator + Trash) with dodge windows.
    - aesthetic: Centered Floating Dock (height 44) with Tela icon.
    - original: Flush Bottom Panel (height 44).
    """
    _setup_env()

    if theme_id == "mac":
        apple_logo = get_asset_path("icons", "custom-launchers", "apple-logo.svg")
        if not os.path.exists(apple_logo):
            apple_logo = "/usr/share/icons/custom-launchers/apple-logo.svg"

        js = f"""
var ps = panels();
var primary = null;
var extraPanels = [];

for (var i = 0; i < ps.length; i++) {{
    var ws = ps[i].widgets();
    var hasTray = false;
    for (var j = 0; j < ws.length; j++) {{
        if (ws[j].type == "org.kde.plasma.systemtray") {{
            hasTray = true;
            break;
        }}
    }}
    if (hasTray && !primary) {{
        primary = ps[i];
    }} else {{
        extraPanels.push(ps[i]);
    }}
}}
if (!primary && ps.length > 0) primary = ps[0];

var launchers = "";
for (var i = 0; i < extraPanels.length; i++) {{
    var ews = extraPanels[i].widgets();
    for (var j = 0; j < ews.length; j++) {{
        if (ews[j].type == "org.kde.plasma.icontasks") {{
            ews[j].currentConfigGroup = ["General"];
            launchers = ews[j].readConfig("launchers");
        }}
    }}
    extraPanels[i].remove();
}}

if (primary) {{
    var ws = primary.widgets();
    for (var i = 0; i < ws.length; i++) {{
        if (ws[i].type == "org.kde.plasma.icontasks") {{
            if (!launchers) {{
                ws[i].currentConfigGroup = ["General"];
                launchers = ws[i].readConfig("launchers");
            }}
            ws[i].remove();
        }} else if (ws[i].type == "org.kde.plasma.pager" || ws[i].type == "org.kde.plasma.showdesktop") {{
            ws[i].remove();
        }} else if (ws[i].type == "org.kde.plasma.kickoff") {{
            ws[i].currentConfigGroup = ["General"];
            ws[i].writeConfig("icon", "{apple_logo}");
        }}
    }}

    primary.location = "top";
    primary.height = 30;
    primary.floating = false;
    primary.lengthMode = "fill";

    var appmenuWidget = null;
    var kickoffWidget = null;
    var trayWidget = null;
    var clockWidget = null;
    var spacerWidget = null;
    var curWs = primary.widgets();
    for (var i = 0; i < curWs.length; i++) {{
        if (curWs[i].type == "org.kde.plasma.appmenu") appmenuWidget = curWs[i];
        else if (curWs[i].type == "org.kde.plasma.kickoff") kickoffWidget = curWs[i];
        else if (curWs[i].type == "org.kde.plasma.systemtray") trayWidget = curWs[i];
        else if (curWs[i].type == "org.kde.plasma.digitalclock") clockWidget = curWs[i];
        else if (curWs[i].type == "org.kde.plasma.panelspacer") {{
            if (!spacerWidget) spacerWidget = curWs[i];
            else curWs[i].remove();
        }}
        else if (curWs[i].type == "org.kde.plasma.marginsseparator") curWs[i].remove();
    }}
    if (!appmenuWidget) {{
        appmenuWidget = primary.addWidget("org.kde.plasma.appmenu");
    }}

    // Expanding spacer pushing system tray & clock to the right
    if (!spacerWidget) {{
        spacerWidget = primary.addWidget("org.kde.plasma.panelspacer");
    }}
    spacerWidget.currentConfigGroup = ["General"];
    spacerWidget.writeConfig("expanding", "true");

    // Configure macOS single-line clock format (Day Date Month | Time)
    if (clockWidget) {{
        clockWidget.currentConfigGroup = ["Appearance"];
        clockWidget.writeConfig("showDate", "true");
        clockWidget.writeConfig("dateDisplayFormat", "1");
        clockWidget.writeConfig("dateFormat", "custom");
        clockWidget.writeConfig("customDateFormat", "ddd d MMM");
    }}

    // Order top bar widgets: Apple Kickoff -> AppMenu -> Spacer -> SystemTray -> Clock
    var orderList = [];
    if (kickoffWidget) orderList.push(kickoffWidget.id);
    if (appmenuWidget) orderList.push(appmenuWidget.id);
    if (spacerWidget) orderList.push(spacerWidget.id);
    if (trayWidget) orderList.push(trayWidget.id);
    if (clockWidget) orderList.push(clockWidget.id);

    primary.currentConfigGroup = ["General"];
    primary.writeConfig("AppletOrder", orderList.join(";"));
    print("ORDER:" + primary.id + ":" + orderList.join(";"));
    if (kickoffWidget) {{
        print("KICKOFF:" + primary.id + ":" + kickoffWidget.id + ":{apple_logo}");
    }}
    primary.reloadConfig();
}}

// Insert Launchpad into launchers if not present
if (launchers && launchers.indexOf("launchpad.desktop") === -1) {{
    launchers = "applications:launchpad.desktop," + launchers;
}}

var dock = new Panel;
dock.location = "bottom";
dock.height = 62;
dock.floating = true;
dock.lengthMode = "fit";
dock.minimumLength = 0;
dock.maximumLength = 2194;
dock.alignment = "center";
dock.hiding = "dodgewindows";

var dockTasks = dock.addWidget("org.kde.plasma.icontasks");
if (launchers) {{
    dockTasks.currentConfigGroup = ["General"];
    dockTasks.writeConfig("launchers", launchers);
    dockTasks.writeConfig("fill", "false");
    dockTasks.writeConfig("iconSpacing", "1");
}}
var dockSep = dock.addWidget("org.kde.plasma.marginsseparator");
var dockTrash = dock.addWidget("org.kde.plasma.trash");
dock.currentConfigGroup = ["General"];
var dockOrder = [dockTasks.id, dockSep.id, dockTrash.id];
dock.writeConfig("AppletOrder", dockOrder.join(";"));
print("ORDER:" + dock.id + ":" + dockOrder.join(";"));
"""

    elif theme_id == "windows":
        win_logo = get_asset_path("icons", "custom-launchers", "windows11-start.svg")
        if not os.path.exists(win_logo):
            win_logo = "/usr/share/icons/custom-launchers/windows11-start.svg"

        js = f"""
var ps = panels();
var primary = null;
var extraPanels = [];

for (var i = 0; i < ps.length; i++) {{
    var ws = ps[i].widgets();
    var hasTray = false;
    for (var j = 0; j < ws.length; j++) {{
        if (ws[j].type == "org.kde.plasma.systemtray") {{
            hasTray = true;
            break;
        }}
    }}
    if (hasTray && !primary) {{
        primary = ps[i];
    }} else {{
        extraPanels.push(ps[i]);
    }}
}}
if (!primary && ps.length > 0) primary = ps[0];

var launchers = "";
for (var i = 0; i < extraPanels.length; i++) {{
    var ews = extraPanels[i].widgets();
    for (var j = 0; j < ews.length; j++) {{
        if (ews[j].type == "org.kde.plasma.icontasks") {{
            ews[j].currentConfigGroup = ["General"];
            launchers = ews[j].readConfig("launchers");
        }}
    }}
    extraPanels[i].remove();
}}

// Strip macOS launchpad if present in launchers
if (launchers) {{
    launchers = launchers.replace("applications:launchpad.desktop,", "").replace("applications:launchpad.desktop", "");
}}

if (primary) {{
    primary.location = "bottom";
    primary.height = 48;
    primary.floating = false;
    primary.lengthMode = "fill";
    primary.alignment = "center";
    primary.hiding = "none";

    var kickoffWidget = null;
    var tasksWidget = null;
    var trayWidget = null;
    var clockWidget = null;
    var spacers = [];

    var ws = primary.widgets();
    for (var i = 0; i < ws.length; i++) {{
        var t = ws[i].type;
        if (t == "org.kde.plasma.kickoff") kickoffWidget = ws[i];
        else if (t == "org.kde.plasma.icontasks") {{
            tasksWidget = ws[i];
            if (!launchers) {{
                ws[i].currentConfigGroup = ["General"];
                launchers = ws[i].readConfig("launchers");
            }}
        }}
        else if (t == "org.kde.plasma.systemtray") trayWidget = ws[i];
        else if (t == "org.kde.plasma.digitalclock") clockWidget = ws[i];
        else if (t == "org.kde.plasma.panelspacer") spacers.push(ws[i]);
        else if (t == "org.kde.plasma.appmenu" || t == "org.kde.plasma.marginsseparator" || t == "org.kde.plasma.trash" || t == "org.kde.plasma.pager" || t == "org.kde.plasma.showdesktop") {{
            ws[i].remove();
        }}
    }}

    if (launchers) {{
        launchers = launchers.replace("applications:launchpad.desktop,", "").replace("applications:launchpad.desktop", "");
    }}

    if (!kickoffWidget) kickoffWidget = primary.addWidget("org.kde.plasma.kickoff");
    kickoffWidget.currentConfigGroup = ["General"];
    kickoffWidget.writeConfig("icon", "{win_logo}");

    if (!tasksWidget) tasksWidget = primary.addWidget("org.kde.plasma.icontasks");
    tasksWidget.currentConfigGroup = ["General"];
    if (launchers) {{
        tasksWidget.writeConfig("launchers", launchers);
    }}
    tasksWidget.writeConfig("fill", "false");
    tasksWidget.writeConfig("iconSpacing", "1");

    if (!trayWidget) trayWidget = primary.addWidget("org.kde.plasma.systemtray");
    if (!clockWidget) clockWidget = primary.addWidget("org.kde.plasma.digitalclock");

    var spacer1 = spacers.length > 0 ? spacers[0] : primary.addWidget("org.kde.plasma.panelspacer");
    var spacer2 = spacers.length > 1 ? spacers[1] : primary.addWidget("org.kde.plasma.panelspacer");

    for (var i = 2; i < spacers.length; i++) {{
        spacers[i].remove();
    }}

    spacer1.currentConfigGroup = ["General"];
    spacer1.writeConfig("expanding", "true");
    spacer2.currentConfigGroup = ["General"];
    spacer2.writeConfig("expanding", "true");

    clockWidget.currentConfigGroup = ["Appearance"];
    clockWidget.writeConfig("showDate", "true");
    clockWidget.writeConfig("dateDisplayFormat", "2");
    clockWidget.writeConfig("dateFormat", "shortDate");

    // Order: Spacer1 -> Windows Start -> Apps -> Spacer2 -> System Tray -> Clock (right aligned)
    var orderList = [spacer1.id, kickoffWidget.id, tasksWidget.id, spacer2.id, trayWidget.id, clockWidget.id];

    primary.currentConfigGroup = ["General"];
    primary.writeConfig("AppletOrder", orderList.join(";"));
    print("ORDER:" + primary.id + ":" + orderList.join(";"));
    if (kickoffWidget) {{
        print("KICKOFF:" + primary.id + ":" + kickoffWidget.id + ":{win_logo}");
    }}
    primary.reloadConfig();
}}
"""

    elif theme_id == "aesthetic":
        modern_logo = get_asset_path("icons", "custom-launchers", "modern-start.svg")
        if not os.path.exists(modern_logo):
            repo_icon = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "custom-launchers", "modern-start.svg"))
            if os.path.exists(repo_icon):
                modern_logo = repo_icon
            else:
                modern_logo = "/usr/share/icons/custom-launchers/modern-start.svg"
                if not os.path.exists(modern_logo):
                    modern_logo = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/modern-start.svg")

        js = f"""
var ps = panels();
var primary = null;
var extraPanels = [];
for (var i = 0; i < ps.length; i++) {{
    var ws = ps[i].widgets();
    var hasTray = false;
    for (var j = 0; j < ws.length; j++) {{
        if (ws[j].type == "org.kde.plasma.systemtray") {{
            hasTray = true;
            break;
        }}
    }}
    if (hasTray && !primary) {{
        primary = ps[i];
    }} else {{
        extraPanels.push(ps[i]);
    }}
}}
if (!primary && ps.length > 0) primary = ps[0];

var launchers = "";
for (var i = 0; i < extraPanels.length; i++) {{
    var ews = extraPanels[i].widgets();
    for (var j = 0; j < ews.length; j++) {{
        if (ews[j].type == "org.kde.plasma.icontasks") {{
            ews[j].currentConfigGroup = ["General"];
            launchers = ews[j].readConfig("launchers");
        }}
    }}
    extraPanels[i].remove();
}}

if (primary) {{
    primary.location = "bottom";
    primary.height = 44;
    primary.floating = true;
    primary.lengthMode = "fill";
    primary.alignment = "center";

    var kickoffWidget = null;
    var tasksWidget = null;
    var trayWidget = null;
    var clockWidget = null;
    var spacers = [];

    var ws = primary.widgets();
    for (var i = 0; i < ws.length; i++) {{
        var t = ws[i].type;
        if (t == "org.kde.plasma.icontasks") {{
            tasksWidget = ws[i];
            if (launchers) {{
                ws[i].currentConfigGroup = ["General"];
                ws[i].writeConfig("launchers", launchers);
            }}
        }} else if (t == "org.kde.plasma.kickoff") {{
            kickoffWidget = ws[i];
            ws[i].currentConfigGroup = ["General"];
            ws[i].writeConfig("icon", "{modern_logo}");
        }} else if (t == "org.kde.plasma.systemtray") trayWidget = ws[i];
        else if (t == "org.kde.plasma.digitalclock") clockWidget = ws[i];
        else if (t == "org.kde.plasma.panelspacer") spacers.push(ws[i]);
        else if (t == "org.kde.plasma.appmenu") {{
            ws[i].remove();
        }}
    }}
    if (!tasksWidget) {{
        tasksWidget = primary.addWidget("org.kde.plasma.icontasks");
        if (launchers) {{
            tasksWidget.currentConfigGroup = ["General"];
            tasksWidget.writeConfig("launchers", launchers);
        }}
    }}
    if (!kickoffWidget) {{
        kickoffWidget = primary.addWidget("org.kde.plasma.kickoff");
        kickoffWidget.currentConfigGroup = ["General"];
        kickoffWidget.writeConfig("icon", "{modern_logo}");
    }}
    if (!trayWidget) trayWidget = primary.addWidget("org.kde.plasma.systemtray");
    if (!clockWidget) clockWidget = primary.addWidget("org.kde.plasma.digitalclock");

    var spacer1 = spacers.length > 0 ? spacers[0] : primary.addWidget("org.kde.plasma.panelspacer");
    var spacer2 = spacers.length > 1 ? spacers[1] : primary.addWidget("org.kde.plasma.panelspacer");
    for (var i = 2; i < spacers.length; i++) {{
        spacers[i].remove();
    }}
    spacer1.currentConfigGroup = ["General"];
    spacer1.writeConfig("expanding", "true");
    spacer2.currentConfigGroup = ["General"];
    spacer2.writeConfig("expanding", "true");

    if (clockWidget) {{
        clockWidget.currentConfigGroup = ["Appearance"];
        clockWidget.writeConfig("showDate", "true");
        clockWidget.writeConfig("dateFormat", "custom");
        clockWidget.writeConfig("customDateFormat", "ddd, MMM d  •  HH:mm");
    }}

    var orderList = [spacer1.id, kickoffWidget.id, tasksWidget.id, spacer2.id, trayWidget.id, clockWidget.id];
    primary.currentConfigGroup = ["General"];
    primary.writeConfig("AppletOrder", orderList.join(";"));
    print("ORDER:" + primary.id + ":" + orderList.join(";"));
    if (kickoffWidget) {{
        print("KICKOFF:" + primary.id + ":" + kickoffWidget.id + ":{modern_logo}");
    }}
    primary.reloadConfig();
}}
"""
    else:
        return

    res = subprocess.run(["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "evaluateScript", js], capture_output=True, text=True)

    orders = {}
    kickoffs = {}
    for line in res.stdout.splitlines():
        if line.startswith("ORDER:"):
            parts = line.split(":")
            if len(parts) >= 3:
                orders[parts[1]] = parts[2]
        elif line.startswith("KICKOFF:"):
            parts = line.split(":")
            if len(parts) >= 4:
                kickoffs[parts[1]] = (parts[2], parts[3])

    if orders or kickoffs:
        ret = subprocess.call(["systemctl", "--user", "stop", "plasma-plasmashell"], stderr=subprocess.DEVNULL)
        if ret != 0:
            subprocess.call(["kquitapp6", "plasmashell"], stderr=subprocess.DEVNULL)
            time.sleep(0.5)

        for cid, applet_order in orders.items():
            subprocess.call([
                "kwriteconfig6",
                "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                "--group", "Containments",
                "--group", str(cid),
                "--group", "General",
                "--key", "AppletOrder",
                applet_order
            ])

        for cid, (kid, icon_path) in kickoffs.items():
            if kid and icon_path:
                subprocess.call([
                    "kwriteconfig6",
                    "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                    "--group", "Containments",
                    "--group", str(cid),
                    "--group", "Applets",
                    "--group", str(kid),
                    "--group", "Configuration",
                    "--group", "General",
                    "--key", "icon",
                    icon_path
                ])

        ret = subprocess.call(["systemctl", "--user", "start", "plasma-plasmashell"], stderr=subprocess.DEVNULL)
        if ret != 0:
            subprocess.Popen(["kstart", "plasmashell"], stderr=subprocess.DEVNULL)
        time.sleep(1)


def _apply_kde(theme_id: str) -> bool:
    """Apply theme settings for KDE Plasma 6 cleanly without killing plasmashell."""
    _setup_env()
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    # 1. Colorscheme, Accent & Desktop Theme (Panel)
    subprocess.call(["plasma-apply-colorscheme", "BreezeDark", "-a", theme["color"]], stderr=subprocess.DEVNULL)
    if theme_id == "mac":
        ensure_whitesur_icons()
        ensure_kde_plasma_theme()
        ensure_launchpad_desktop()
        subprocess.call(["plasma-apply-desktoptheme", "WhiteSur-dark"], stderr=subprocess.DEVNULL)
    elif theme_id == "windows":
        ensure_win11_icons()
        ensure_windows_start_icon()
        subprocess.call(["plasma-apply-desktoptheme", "breeze-dark"], stderr=subprocess.DEVNULL)
    elif theme_id == "aesthetic":
        ensure_tela_icons()
        ensure_modern_start_icon()
        subprocess.call(["plasma-apply-desktoptheme", "breeze-dark"], stderr=subprocess.DEVNULL)
    else:
        subprocess.call(["plasma-apply-desktoptheme", "breeze-dark"], stderr=subprocess.DEVNULL)

    # 2. Icons & Cursors
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", theme["icon_theme"]])
    subprocess.call(["plasma-apply-cursortheme", theme["cursor_theme"]], stderr=subprocess.DEVNULL)

    # 3. Typography & Subpixel Rendering
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "font", "Inter,10.5,-1,5,50,0,0,0,0,0"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "fixed", "JetBrains Mono,10.5,-1,5,50,0,0,0,0,0"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "WM", "--key", "activeFont", "Inter Semi-Bold,10.5,-1,5,75,0,0,0,0,0"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "XftAntialias", "true"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "XftHintStyle", "hintslight"])
    subprocess.call(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "XftSubPixel", "rgb"])

    # 4. Window Buttons
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnLeft", theme["button_layout_kde_left"]])
    subprocess.call(["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnRight", theme["button_layout_kde_right"]])

    # 5. Wallpaper
    if "wallpaper" in theme and theme["wallpaper"]:
        wall_path = get_asset_path(*theme["wallpaper"])
    else:
        wall_path = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))
    subprocess.call(["plasma-apply-wallpaperimage", wall_path], stderr=subprocess.DEVNULL)

    # 6. Configure Lower Panel (Centering, Height, Floating, Start Icon)
    _configure_kde_panel(theme_id)

    # 7. Sync GSettings & GTK 3/4 settings for GTK apps running on KDE
    if theme_id == "mac":
        gtk_layout = "close,minimize,maximize:"
    elif theme_id == "windows":
        gtk_layout = "appmenu:minimize,maximize,close"
    else:
        gtk_layout = "appmenu:close"

    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"], button_layout=gtk_layout)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Breeze-Dark"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme["icon_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme["cursor_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", gtk_layout], stderr=subprocess.DEVNULL)

    # 7. Live KWin & DBus reload
    subprocess.call(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], stderr=subprocess.DEVNULL)
    _reload_kde_icons()

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
    _setup_env()

    # 1. Gracefully stop plasma-plasmashell service
    subprocess.call(["systemctl", "--user", "stop", "plasma-plasmashell"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    # 2. Restore pristine backup files
    if os.path.exists(BACKUP_DIR_KDE):
        for cfg in ["plasma-org.kde.plasma.desktop-appletsrc", "kdeglobals", "kwinrc", "plasmarc"]:
            src = os.path.join(BACKUP_DIR_KDE, cfg)
            dst = os.path.expanduser(f"~/.config/{cfg}")
            if os.path.exists(src):
                shutil.copy2(src, dst)

    # 3. Restart plasma-plasmashell service cleanly
    subprocess.call(["systemctl", "--user", "start", "plasma-plasmashell"], stderr=subprocess.DEVNULL)
    time.sleep(2)

    # 4. Reconfigure KWin
    subprocess.call(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], stderr=subprocess.DEVNULL)

    # 5. Restore stock colors, desktop theme, and cursor
    subprocess.call(["plasma-apply-colorscheme", "BreezeLight"], stderr=subprocess.DEVNULL)
    subprocess.call(["plasma-apply-cursortheme", "breeze_cursors"], stderr=subprocess.DEVNULL)
    res = subprocess.call(["plasma-apply-desktoptheme", "default"], stderr=subprocess.DEVNULL)
    if res != 0:
        subprocess.call(["plasma-apply-desktoptheme", "breeze-light"], stderr=subprocess.DEVNULL)

    # Reset panel geometry to stock Debian flush dock
    js = """
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    ps[i].height = 44;
    ps[i].floating = false;
    ps[i].lengthMode = "fill";
    ps[i].hiding = "none";
}
"""
    subprocess.call(["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "evaluateScript", js], stderr=subprocess.DEVNULL)

    # 6. Revert GTK & GSettings
    sync_gtk_settings(dark_mode=False, icon_theme="breeze", cursor_theme="breeze_cursors", button_layout="appmenu:close")
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "default"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Breeze"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "breeze"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", "breeze_cursors"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", "appmenu:close"], stderr=subprocess.DEVNULL)

    # 7. Broadcast changes & sycoca reload
    _reload_kde_icons()
    return True


def _apply_cinnamon(theme_id: str) -> bool:
    """Apply theme settings for Cinnamon (Linux Mint)."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    if theme_id == "mac":
        ensure_whitesur_icons()
    elif theme_id == "windows":
        ensure_win11_icons()
        ensure_windows_start_icon()
    elif theme_id == "aesthetic":
        ensure_tela_icons()
        ensure_modern_start_icon()

    # 1. Interface themes
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "icon-theme", theme["icon_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "cursor-theme", theme["cursor_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "font-name", "Inter 10"], stderr=subprocess.DEVNULL)

    # 2. GTK theme & Dark style
    gtk_theme = "Mint-Y-Dark" if theme_id in ["windows", "aesthetic", "mac"] else "Mint-Y"
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "gtk-theme", gtk_theme], stderr=subprocess.DEVNULL)

    # 3. Window controls button layout
    if theme_id == "mac":
        layout = "close,minimize,maximize:"
    elif theme_id == "windows":
        layout = ":minimize,maximize,close"
    else:
        layout = ":minimize,maximize,close"
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.wm.preferences", "button-layout", layout], stderr=subprocess.DEVNULL)

    # 4. Wallpaper
    if "wallpaper" in theme and theme["wallpaper"]:
        wall_path = get_asset_path(*theme["wallpaper"])
    else:
        wall_path = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", f"file://{wall_path}"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", "zoom"], stderr=subprocess.DEVNULL)

    # 5. Cross-toolkit GTK sync
    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"], button_layout=layout)
    _apply_ghostty_theme(theme_id)
    return True


def _revert_cinnamon() -> bool:
    """Revert Cinnamon to stock defaults."""
    backup_file = os.path.join(BACKUP_DIR_CINNAMON, "cinnamon-backup.dconf")
    if os.path.exists(backup_file):
        try:
            with open(backup_file, "r") as f:
                subprocess.run(["dconf", "load", "/org/cinnamon/"], stdin=f, check=True)
            return True
        except Exception:
            pass

    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "icon-theme", "Mint-Y"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "cursor-theme", "Bibata-Modern-Classic"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.interface", "gtk-theme", "Mint-Y"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.cinnamon.desktop.wm.preferences", "button-layout", ":minimize,maximize,close"], stderr=subprocess.DEVNULL)
    sync_gtk_settings(dark_mode=False, icon_theme="Mint-Y", cursor_theme="Bibata-Modern-Classic", button_layout=":minimize,maximize,close")
    return True


def _apply_xfce(theme_id: str) -> bool:
    """Apply theme settings for XFCE."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    if theme_id == "mac":
        ensure_whitesur_icons()
    elif theme_id == "windows":
        ensure_win11_icons()
        ensure_windows_start_icon()
    elif theme_id == "aesthetic":
        ensure_tela_icons()
        ensure_modern_start_icon()

    # 1. Icons & Cursors
    subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", theme["icon_theme"], "--create", "-t", "string"], stderr=subprocess.DEVNULL)
    subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/CursorThemeName", "-s", theme["cursor_theme"], "--create", "-t", "string"], stderr=subprocess.DEVNULL)
    subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Gtk/FontName", "-s", "Inter 10", "--create", "-t", "string"], stderr=subprocess.DEVNULL)

    # 2. Window manager buttons (xfwm4: C=Close, M=Maximize, H=Hide/Minimize, |=Title)
    if theme_id == "mac":
        btn_layout = "CMH|"
        gtk_layout = "close,minimize,maximize:"
    elif theme_id == "windows":
        btn_layout = "|HMC"
        gtk_layout = "appmenu:minimize,maximize,close"
    else:
        btn_layout = "|HMC"
        gtk_layout = "appmenu:close"

    subprocess.call(["xfconf-query", "-c", "xfwm4", "-p", "/general/button_layout", "-s", btn_layout, "--create", "-t", "string"], stderr=subprocess.DEVNULL)

    # 3. Wallpaper
    if "wallpaper" in theme and theme["wallpaper"]:
        wall_path = get_asset_path(*theme["wallpaper"])
    else:
        wall_path = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))

    try:
        props = subprocess.check_output(["xfconf-query", "-c", "xfce4-desktop", "-l"], text=True, stderr=subprocess.DEVNULL).splitlines()
        for p in props:
            if "last-image" in p:
                subprocess.call(["xfconf-query", "-c", "xfce4-desktop", "-p", p, "-s", wall_path], stderr=subprocess.DEVNULL)
    except Exception:
        subprocess.call(["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/workspace0/last-image", "-s", wall_path, "--create", "-t", "string"], stderr=subprocess.DEVNULL)

    # 4. Cross-toolkit GTK sync
    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"], button_layout=gtk_layout)
    _apply_ghostty_theme(theme_id)
    return True


def _revert_xfce() -> bool:
    """Revert XFCE to stock defaults."""
    subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "elementary-xfce-darker"], stderr=subprocess.DEVNULL)
    subprocess.call(["xfconf-query", "-c", "xsettings", "-p", "/Net/CursorThemeName", "-s", "default"], stderr=subprocess.DEVNULL)
    subprocess.call(["xfconf-query", "-c", "xfwm4", "-p", "/general/button_layout", "-s", "|HMC"], stderr=subprocess.DEVNULL)
    sync_gtk_settings(dark_mode=False, icon_theme="elementary-xfce-darker", cursor_theme="default", button_layout="|HMC")
    return True


def _apply_mate(theme_id: str) -> bool:
    """Apply theme settings for MATE desktop."""
    theme = next((t for t in THEMES if t["id"] == theme_id), None)
    if not theme:
        return False

    if theme_id == "mac":
        ensure_whitesur_icons()
    elif theme_id == "windows":
        ensure_win11_icons()
        ensure_windows_start_icon()
    elif theme_id == "aesthetic":
        ensure_tela_icons()
        ensure_modern_start_icon()

    subprocess.call(["gsettings", "set", "org.mate.interface", "icon-theme", theme["icon_theme"]], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.mate.peripherals-mouse", "cursor-theme", theme["cursor_theme"]], stderr=subprocess.DEVNULL)

    if theme_id == "mac":
        layout = "close,minimize,maximize:"
    elif theme_id == "windows":
        layout = ":minimize,maximize,close"
    else:
        layout = ":close"
    subprocess.call(["gsettings", "set", "org.mate.Marco.general", "button-layout", layout], stderr=subprocess.DEVNULL)

    if "wallpaper" in theme and theme["wallpaper"]:
        wall_path = get_asset_path(*theme["wallpaper"])
    else:
        wall_path = get_asset_path(*theme.get("wallpaper_dark", ("backgrounds", "aesthetic", "calm-night.png")))
    subprocess.call(["gsettings", "set", "org.mate.background", "picture-filename", wall_path], stderr=subprocess.DEVNULL)

    sync_gtk_settings(dark_mode=True, icon_theme=theme["icon_theme"], cursor_theme=theme["cursor_theme"], button_layout=layout)
    _apply_ghostty_theme(theme_id)
    return True


def _revert_mate() -> bool:
    """Revert MATE to stock defaults."""
    backup_file = os.path.join(BACKUP_DIR_MATE, "mate-backup.dconf")
    if os.path.exists(backup_file):
        try:
            with open(backup_file, "r") as f:
                subprocess.run(["dconf", "load", "/org/mate/"], stdin=f, check=True)
            return True
        except Exception:
            pass

    subprocess.call(["gsettings", "set", "org.mate.interface", "icon-theme", "mate"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.mate.peripherals-mouse", "cursor-theme", "default"], stderr=subprocess.DEVNULL)
    subprocess.call(["gsettings", "set", "org.mate.Marco.general", "button-layout", ":minimize,maximize,close"], stderr=subprocess.DEVNULL)
    sync_gtk_settings(dark_mode=False, icon_theme="mate", cursor_theme="default", button_layout=":minimize,maximize,close")
    return True


def _revert_generic() -> bool:
    """Revert generic environment."""
    sync_gtk_settings(dark_mode=False, icon_theme="Adwaita", cursor_theme="Adwaita")
    return True


def notify_user(title: str, message: str):
    """Deliver a native desktop notification asynchronously without blocking."""
    icon_path = get_asset_path("branding", "io.github.themehub.png")
    icon_arg = f"--icon={icon_path}" if os.path.exists(icon_path) else "--icon=preferences-desktop-theme"
    try:
        subprocess.Popen(
            ["notify-send", "-t", "3000", title, message, icon_arg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
