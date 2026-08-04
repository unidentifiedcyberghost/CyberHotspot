#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[qr]"
echo
echo "CyberHotspot installed in $ROOT/.venv"
echo "Run: $ROOT/.venv/bin/cyberhotspot doctor"
echo "Run GUI: $ROOT/.venv/bin/cyberhotspot-gui"
