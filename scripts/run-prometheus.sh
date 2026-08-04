#!/usr/bin/env bash
set -euo pipefail
PROMETHEUS="${1:-./prometheus}"
CONFIG="${2:-./prometheus/prometheus.yml}"
[[ -x "$PROMETHEUS" ]] || { echo "Prometheus binary not found: $PROMETHEUS" >&2; exit 1; }
[[ -f "$CONFIG" ]] || { echo "CyberHotspot Prometheus config not found: $CONFIG" >&2; exit 1; }
echo "CYBERHOTSPOT // LOCAL PROMETHEUS"
echo "Target: 127.0.0.1:9464"
exec "$PROMETHEUS" "--config.file=$CONFIG"
