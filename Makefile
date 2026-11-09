PREFIX ?= /usr/local
PYTHON ?= python3

.PHONY: all deb install install-user uninstall clean test release

all:
	@echo "Theme Hub Build System"
	@echo "Targets:"
	@echo "  make deb          - Build Debian .deb installer package"
	@echo "  make release      - Build and publish release to GitHub Releases"
	@echo "  make install      - Install system-wide (requires sudo)"
	@echo "  make install-user - Install to ~/.local without root"
	@echo "  make uninstall    - Uninstall from system"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make test         - Run CLI diagnostics"

deb:
	./build.sh

release:
	./release.sh

install:
	./install.sh --system

install-user:
	./install.sh --user

uninstall:
	./uninstall.sh --system

clean:
	rm -rf build dist

test:
	$(PYTHON) src/bin/theme-hub-cli info
	$(PYTHON) src/bin/theme-hub-cli list
