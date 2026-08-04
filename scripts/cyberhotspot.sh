#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

if command -v cyberhotspot >/dev/null 2>&1; then
  exec cyberhotspot "$@"
fi

if [[ -x "$APP_DIR/.venv/bin/python" ]]; then
  exec "$APP_DIR/.venv/bin/python" -m cyberhotspot.cli "$@"
fi

exec "$PYTHON" -m cyberhotspot.cli "$@"
