"""Theme Card component for Theme Hub."""
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango


class ThemeCard(Adw.ActionRow):
    def __init__(self, theme_data, on_apply_callback):
        super().__init__()
        self.theme_data = theme_data
        self.theme_id = theme_data["id"]
        self.on_apply_callback = on_apply_callback

        self.set_title(theme_data["title"])
        self.set_subtitle(theme_data["subtitle"])
        self.set_subtitle_lines(3)

        # Leading Icon (supports direct SVG file path or theme icon name)
        icon_val = theme_data.get("icon", "")
        if icon_val and os.path.exists(icon_val):
            icon_img = Gtk.Image.new_from_file(icon_val)
        else:
            icon_img = Gtk.Image.new_from_icon_name(icon_val or "image-missing")
        icon_img.set_pixel_size(36)
        icon_img.set_margin_start(8)
        icon_img.set_margin_end(8)
        self.add_prefix(icon_img)

        # Suffix container
        self.suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.suffix_box.set_valign(Gtk.Align.CENTER)
        self.add_suffix(self.suffix_box)

        # Active Badge
        self.badge = Gtk.Label(label="ACTIVE")
        self.badge.add_css_class("badge")
        self.badge.add_css_class("accent")
        self.badge.add_css_class("caption-heading")
        self.badge.set_visible(False)
        self.suffix_box.append(self.badge)

        # Spinner (for in-flight applying)
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        self.suffix_box.append(self.spinner)

        # Apply / Revert Action Button
        self.action_btn = Gtk.Button()
        if self.theme_id == "original":
            self.action_btn.set_label("Revert")
            self.action_btn.add_css_class("destructive-action")
        else:
            self.action_btn.set_label("Apply")
            self.action_btn.add_css_class("suggested-action")

        self.action_btn.connect("clicked", self._on_btn_clicked)
        self.suffix_box.append(self.action_btn)

    def set_active_state(self, is_active: bool):
        """Update active badge and button visual state."""
        self.badge.set_visible(is_active)
        if is_active:
            self.add_css_class("accent-card")
            if self.theme_id != "original":
                self.action_btn.set_label("Applied")
                self.action_btn.set_sensitive(False)
            else:
                self.action_btn.set_label("Revert")
                self.action_btn.set_sensitive(True)
        else:
            self.remove_css_class("accent-card")
            self.action_btn.set_sensitive(True)
            if self.theme_id == "original":
                self.action_btn.set_label("Revert")
            else:
                self.action_btn.set_label("Apply")

    def set_loading(self, loading: bool):
        """Toggle spinner and button interactivity."""
        self.spinner.set_visible(loading)
        if loading:
            self.spinner.start()
            self.action_btn.set_sensitive(False)
        else:
            self.spinner.stop()
            self.action_btn.set_sensitive(True)

    def _on_btn_clicked(self, button):
        self.on_apply_callback(self, self.theme_data)
