# Installation Guide — CyberHotspot

This file covers installation on major distributions, installing dependencies, and system setup.

Prerequisites
- A Linux system with NetworkManager (recommended) or the ability to run hostapd.
- Python 3.8+
- sudo/root permissions for hotspot operations.

Common packages (Debian/Ubuntu)
sudo apt update
sudo apt install -y python3 python3-pip network-manager qrencode build-essential libssl-dev pkg-config

Install Python requirements
python3 -m pip install --user -r requirements.txt

Optional (for building protected builds)
sudo apt install -y python3-dev gcc
python3 -m pip install cython pyinstaller pyarmor

Install system-wide (example)
sudo make install

Notes for Fedora
sudo dnf install python3 python3-pip NetworkManager qrencode
python3 -m pip install --user -r requirements.txt

Notes for Arch
sudo pacman -S python python-pip networkmanager qrencode
python3 -m pip install --user -r requirements.txt

Enabling NetworkManager
- Ensure NetworkManager service is running:
  sudo systemctl enable --now NetworkManager