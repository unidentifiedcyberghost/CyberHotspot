# CyberHotspot

A powerful, modern Wi‑Fi hotspot tool for Linux — Terminal + PyQt5 GUI — Python + Bash.

Run the colorful terminal banner:
- cat BANNER.txt
- or python3 banner_print.py (best cross-platform)

Version: 0.1.0

Summary
- Create and manage Wi‑Fi hotspots from a laptop or VM.
- Two editions: Terminal (CLI) and GUI (PyQt5).
- Primary backend: NetworkManager (nmcli). Advanced fallback: hostapd + dnsmasq scaffolding.
- Features: QR code generation, client listing, MAC filter hooks, IPv4 sharing, VM tips, packaging helpers, and optional code protection/obfuscation pipeline.

Quicklinks
- CLI: cyberhotspot-cli
- GUI: cyberhotspot-gui
- Banner: BANNER.txt
- Docs: docs/

Quickstart (developer)
1. Clone the repository:
   git clone https://github.com/<your-username>/CyberHotspot.git
   cd CyberHotspot
2. Install system deps (example for Debian/Ubuntu):
   sudo apt update
   sudo apt install -y python3 python3-pip network-manager qrencode build-essential
3. Install Python deps:
   python3 -m pip install -r requirements.txt
4. Try the banner:
   python3 banner_print.py
5. Try the CLI (requires root for hotspot operations):
   sudo cyberhotspot-cli start --ssid "CyberNet" --passwd "SecretPass123"
   sudo cyberhotspot-cli status
   sudo cyberhotspot-cli stop
6. Run GUI:
   python3 -m cyberhotspot.gui
   or after install: cyberhotspot-gui

Important notes
- Many hotspot operations require root or appropriate capabilities (NetworkManager actions, hostapd, iptables/nftables).
- Running a hotspot inside a VM typically requires passing a Wi‑Fi device into the VM (USB passthrough) or bridging on the host — see docs/VIRTUAL_MACHINE.md.
- The repository includes optional guidance for making release binaries and obfuscating/protecting Python code (see docs/ENCRYPTION.md). There is no perfect copy-proof solution for interpreted languages; the goal is to raise the difficulty level.

Repository layout (important files)
- BANNER.txt — colorful terminal banner
- banner_print.py — colorama-based renderer
- Makefile — install/uninstall helper
- requirements.txt
- cyberhotspot/ (Python package)
  - backend.py, cli.py, gui.py, __init__.py
- scripts/cyberhotspot.sh — bash wrapper
- docs/ — full user & developer guides
- LICENSE (MIT by default)
- CONTRIBUTING.md

Support and contributing
- See CONTRIBUTING.md for contribution process.
- For bug reports and feature requests, open issues on the repository.

License
- MIT (see LICENSE)
