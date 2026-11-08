# Theme Hub 🎨

**Theme Hub** is an all-in-one handcrafted desktop appearance studio and theme switcher for Linux. Built with modern GTK 4 and Libadwaita, it enables instant switching between four distinct desktop environments with a single click, complete with authentic wallpapers, icon suites, typography, floating docks, and titlebar window controls.

---

## 🌟 Features

- **Four Handcrafted Environments**:
  - 🎨 **Modern Aesthetic**: Dark minimalist look with Inter typography, Tela Circle icons, floating centered dock, and Calm Night 4K wallpaper.
  - 🪟 **Windows 11 Look**: Authentic Windows 11 Fluent look with Win11 icons, Bloom 4K wallpaper, right-aligned controls (`minimize,maximize,close`), and centered taskbar.
  - 🍎 **macOS Sonoma Look**: Sonoma 4K wallpapers, WhiteSur icons, macOS traffic-light buttons on the left (`close,minimize,maximize`), and floating bottom dock with Launchpad.
  - 🔄 **Original Stock Defaults**: Safe, one-click restoration to default system settings without losing personal data or applications.
- **Universal Desktop Environment Support**:
  - **GNOME Shell (46, 47, 48)**: Manages GSettings, window controls, wallpaper, Dash-to-Panel, and Ghostty terminal styling.
  - **KDE Plasma 6 / 5**: Live in-memory reconfiguration via DBus (`org.kde.KWin`), `plasma-apply-*`, `kwriteconfig6`, and GTK dark mode synchronization (zero `plasmashell` crashes).
  - **Wayland & X11**: Full native support for both display architectures.
- **Unified Interfaces**:
  - 🖥️ **Modern GUI App**: Visual cards, DE detection badge, real-time "ACTIVE" indicators, and toast status notifications.
  - 💻 **CLI Tool (`theme-hub-cli`)**: Full terminal interface for scripting, headless use, or hotkey binding.
- **100% Offline & Self-Contained**:
  - Bundles all 4K wallpapers, icon suites, cursor sets, and fonts directly inside the package.

---

## 📦 Installation Options

### Option 1: Install via Debian Package (.deb) (Recommended for Debian/Ubuntu/Mint)

You can build and install the native Debian package:

```bash
cd ~/Development/theme-hub

# Build .deb package (creates dist/theme-hub_1.0.0_all.deb)
./build.sh

# Install via apt
sudo apt install ./dist/theme-hub_1.0.0_all.deb
```

### Option 2: System-Wide Installer Script

Works on any Linux distribution (Debian, Ubuntu, Fedora, Arch, openSUSE):

```bash
cd ~/Development/theme-hub
sudo ./install.sh --system
```

### Option 3: User-Level Installation (No Root / Sudo Required)

Installs entirely into your `~/.local` directory:

```bash
cd ~/Development/theme-hub
./install.sh --user
```

---

## 🚀 Usage

### Launching the GUI App
- From your application launcher / app menu: search for **Theme Hub**.
- From terminal:
  ```bash
  theme-hub
  ```

### Using the Command Line Interface (`theme-hub-cli`)

The included `theme-hub-cli` allows managing themes from any terminal, shell script, or shortcut:

```bash
# Show system diagnostics and active desktop environment
theme-hub-cli info

# List available themes and current active state
theme-hub-cli list

# Apply Modern Aesthetic theme
theme-hub-cli apply aesthetic

# Apply Windows 11 Look
theme-hub-cli apply windows

# Apply macOS Sonoma Look
theme-hub-cli apply mac

# Revert to original stock desktop defaults
theme-hub-cli revert

# Show currently active theme
theme-hub-cli current
```

---

## 🛠️ Project Structure

```
~/Development/theme-hub/
├── assets/                  # Bundled assets (4K wallpapers, icons, cursors, fonts)
│   ├── backgrounds/         # aesthetic, windows, mac wallpapers
│   ├── cursors/             # Bibata-Modern-Classic, macOS cursors
│   ├── fonts/               # Inter, JetBrains Mono font families
│   ├── icons/               # Tela-circle-dark, Win11-dark, WhiteSur-dark
│   └── branding/            # App icon (SVG + PNG) and previews
├── data/                    # Desktop entry and AppStream metainfo
│   ├── io.github.themehub.desktop
│   └── io.github.themehub.metainfo.xml
├── debian/                  # Debian package control & maintenance scripts
│   ├── control
│   ├── postinst
│   └── postrm
├── src/
│   ├── bin/                 # Executable entry points
│   │   ├── theme-hub        # GTK4 GUI launcher
│   │   └── theme-hub-cli    # CLI tool
│   └── theme_hub/           # Core Python package
│       ├── __init__.py
│       ├── app.py           # Libadwaita window & application logic
│       ├── backend.py       # GNOME & KDE Plasma automation engine
│       ├── config.py        # Theme metadata and asset resolution
│       └── ui/
│           ├── __init__.py
│           └── theme_card.py # Custom card component with badges & spinners
├── dist/                    # Built .deb package output directory
├── build.sh                 # Debian package builder
├── install.sh               # Universal installer script (--system / --user)
├── uninstall.sh             # Clean uninstaller script
├── Makefile                 # Make targets (deb, install, install-user, test)
└── README.md                # Project documentation
```

---

## 🗑️ Uninstallation

To remove Theme Hub at any time:

```bash
# If installed via apt/dpkg:
sudo apt remove theme-hub

# If installed via installer script (system):
sudo ./uninstall.sh --system

# If installed in user mode:
./uninstall.sh --user
```

---

## 📄 License

GPL-3.0-or-later. Wallpapers and icon assets retain their respective creative commons / open-source licenses.
