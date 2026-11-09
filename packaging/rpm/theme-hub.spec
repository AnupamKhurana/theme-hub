Name:           theme-hub
Version:        1.0.0
Release:        1%{?dist}
Summary:        Instant desktop aesthetic switcher for Linux desktops

License:        GPLv3+
URL:            https://github.com/AnupamKhurana/theme-hub
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3
Requires:       gtk4
Requires:       python3-gobject
Requires:       libadwaita

%description
Theme Hub delivers instant, pixel-perfect desktop aesthetics for Linux desktops.
Switch between macOS Sonoma, Windows 11, and Modern Minimalist Dark with
authentic icons, fonts, wallpapers, and centered floating panels.

%prep
%autosetup

%build
# No compilation required (pure Python + shell + assets)

%install
rm -rf %{buildroot}
./install.sh --system --destdir %{buildroot}

%files
/usr/local/bin/theme-hub
/usr/local/bin/theme-hub-cli
/usr/local/share/theme-hub
/usr/share/applications/io.github.themehub.desktop
/usr/share/icons/hicolor/*/apps/io.github.themehub.*
/usr/share/fonts/truetype/theme-hub

%changelog
* Mon Nov 09 2026 Anupam Khurana <anupam@example.com> - 1.0.0-1
- Initial release with macOS Sonoma, Windows 11, and Modern Aesthetic themes
- Multi-DE support for KDE Plasma 6, GNOME Shell, Cinnamon, XFCE, and MATE
