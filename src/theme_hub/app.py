"""Main Application and Window for Theme Hub."""
import os
import sys
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

from theme_hub.config import APP_ID, APP_NAME, APP_VERSION, THEMES
from theme_hub.backend import (
    detect_desktop_environment,
    detect_display_server,
    get_current_theme,
    apply_theme
)
from theme_hub.ui.theme_card import ThemeCard

CUSTOM_CSS = b"""
.badge {
    padding: 3px 8px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge.accent {
    background-color: alpha(@accent_color, 0.2);
    color: @accent_color;
}
.de-chip {
    padding: 4px 10px;
    border-radius: 12px;
    background-color: alpha(@window_fg_color, 0.08);
    font-size: 0.8rem;
    font-weight: 600;
}
"""


class ThemeHubWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(760, 680)
        self.set_title(APP_NAME)

        # Detect DE and Display
        self.de_name = detect_desktop_environment().upper()
        self.display_name = detect_display_server()

        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(main_box)

        # Header Bar
        header = Adw.HeaderBar()
        title_widget = Adw.WindowTitle(
            title=APP_NAME,
            subtitle=f"{self.de_name} • {self.display_name} Environment"
        )
        header.set_title_widget(title_widget)

        # DE Badge in Header
        de_label = Gtk.Label(label=f"🖥️ {self.de_name}")
        de_label.add_css_class("de-chip")
        header.pack_start(de_label)

        # About button
        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text("About Theme Hub")
        about_btn.connect("clicked", self._on_about_clicked)
        header.pack_end(about_btn)

        main_box.append(header)

        # Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(720)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        scrolled.set_child(clamp)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        clamp.set_child(content_box)

        # Status Hero Banner
        banner = Adw.StatusPage()
        banner.set_title("Desktop Appearance Studio")
        banner.set_description(
            f"Seamlessly transform your {self.de_name} interface into handcrafted environments. "
            "All changes apply instantly with one-click safe restore."
        )
        banner.set_icon_name("preferences-desktop-theme")
        content_box.append(banner)

        # Theme Group
        self.group = Adw.PreferencesGroup()
        self.group.set_title("Handcrafted Themes")
        self.group.set_description("Select an appearance to transform wallpapers, icons, fonts, docks, and window controls.")
        content_box.append(self.group)

        # Cards
        self.cards = {}
        self.current_theme = get_current_theme()

        for theme in THEMES:
            card = ThemeCard(theme, on_apply_callback=self._handle_apply)
            card.set_active_state(theme["id"] == self.current_theme)
            self.group.add(card)
            self.cards[theme["id"]] = card

    def _handle_apply(self, card_widget, theme_data):
        """Asynchronously apply theme in a background thread."""
        theme_id = theme_data["id"]
        card_widget.set_loading(True)

        # Disable all action buttons during operation
        for c in self.cards.values():
            c.action_btn.set_sensitive(False)

        def worker():
            err_msg = None
            try:
                success = apply_theme(theme_id)
                if not success:
                    err_msg = "Application returned failure"
            except Exception as e:
                err_msg = str(e)

            GLib.idle_add(self._on_apply_finished, theme_id, card_widget, err_msg)

        threading.Thread(target=worker, daemon=True).start()

    def _on_apply_finished(self, theme_id, card_widget, err_msg):
        card_widget.set_loading(False)

        if err_msg:
            toast = Adw.Toast(title=f"Error applying theme: {err_msg}")
            self.toast_overlay.add_toast(toast)
            # Restore button sensitivities
            for tid, c in self.cards.items():
                c.set_active_state(tid == self.current_theme)
            return

        self.current_theme = theme_id
        for tid, c in self.cards.items():
            c.set_active_state(tid == theme_id)

        theme_title = next((t["title"] for t in THEMES if t["id"] == theme_id), theme_id)
        if theme_id == "original":
            toast = Adw.Toast(title="Restored stock system defaults!")
        else:
            toast = Adw.Toast(title=f"Applied {theme_title} successfully!")
        self.toast_overlay.add_toast(toast)

    def _on_about_clicked(self, button):
        about = Adw.AboutWindow(
            transient_for=self,
            application_name=APP_NAME,
            application_icon=APP_ID,
            developer_name="Antigravity Studio",
            version=APP_VERSION,
            website="https://github.com/anupam/theme-hub",
            issue_url="https://github.com/anupam/theme-hub/issues",
            copyright="© 2026 Antigravity",
            license_type=Gtk.License.GPL_3_0,
            comments="Instant aesthetic, Windows 11, and macOS appearance studio for Linux."
        )
        about.present()


class ThemeHubApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_startup(self):
        super().do_startup()
        display = Gdk.Display.get_default()
        if display:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(CUSTOM_CSS)
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ThemeHubWindow(application=self)
        win.present()


def main():
    app = ThemeHubApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
