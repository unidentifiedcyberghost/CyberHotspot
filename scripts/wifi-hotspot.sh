#!/usr/bin/env bash
# Minimal Wi-Fi hotspot helper using NetworkManager (nmcli)
# Usage: sudo ./wifi-hotspot.sh start --ssid MyHotspot --passwd MyPass --ifname wlan0
#        sudo ./wifi-hotspot.sh stop
#        sudo ./wifi-hotspot.sh status

set -euo pipefail

CMD="${1:-}"

# Defaults
IFACE=""
SSID=""
PASS=""
CON_NAME="hotspot-$(date +%s)"

require_nmcli() {
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "Error: nmcli (NetworkManager) is required. Install NetworkManager and nmcli." >&2
    exit 2
  fi
}

print_help() {
  cat <<EOF
wifi-hotspot.sh — minimal hotspot controller using nmcli

Usage:
  sudo $0 start --ssid SSID --passwd PASSWORD [--ifname IFACE] [--shared]
  sudo $0 stop [--con-name NAME]
  sudo $0 status [--con-name NAME]
  sudo $0 help

Options:
  --ssid SSID         Hotspot SSID (required for start)
  --passwd PASSWORD   WPA2 password (min 8 chars) (required for start)
  --ifname IFACE      Wireless interface to use (optional; nmcli auto-detects)
  --shared            Set IPv4 sharing mode for internet (NetworkManager "shared")
  --con-name NAME     Use/stop the given connection name (default auto-generated)

Notes:
  - This script expects NetworkManager managing your interfaces.
  - To view connected devices, run: arp -n or ip neigh show
EOF
}

parse_args() {
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --ssid) SSID="$2"; shift 2;;
      --passwd) PASS="$2"; shift 2;;
      --ifname) IFACE="$2"; shift 2;;
      --shared) SHARED=1; shift;;
      --con-name) CON_NAME="$2"; shift 2;;
      start|stop|status|help) # ignore duplicated
        shift;;
      *) echo "Unknown option: $1"; exit 2;;
    esac
  done
}

start_hotspot() {
  if [[ -z "$SSID" || -z "$PASS" ]]; then
    echo "Error: --ssid and --passwd are required for start" >&2
    exit 2
  fi
  if [[ "${#PASS}" -lt 8 ]]; then
    echo "Error: password must be at least 8 characters" >&2
    exit 2
  fi

  local cmd=(nmcli dev wifi hotspot)
  [[ -n "$IFACE" ]] && cmd+=(ifname "$IFACE")
  cmd+=(ssid "$SSID" password "$PASS")
  echo "Creating hotspot (this will create a connection named like 'Hotspot')..."
  "${cmd[@]}"

  # Find the connection name created by nmcli (usually "Hotspot")
  local created_con
  created_con=$(nmcli -t -f NAME,TYPE connection show --active | awk -F: '$2=="802-11-wireless" {print $1; exit}')
  if [[ -z "$created_con" ]]; then
    echo "Warning: couldn't detect created hotspot connection name. Use nmcli connection show to inspect." >&2
  else
    echo "Hotspot connection active: $created_con"
    echo "To stop: sudo nmcli connection down \"$created_con\" ; sudo nmcli connection delete \"$created_con\""
  fi

  if [[ "${SHARED:-0}" -eq 1 && -n "$created_con" ]]; then
    echo "Setting IPv4 sharing to 'shared' for $created_con..."
    nmcli connection modify "$created_con" ipv4.method shared || true
    nmcli connection up "$created_con" || true
  fi

  echo "Hotspot started."
}

stop_hotspot() {
  local name_arg="${CON_NAME}"
  # If user didn't provide and we can detect an active wifi hotspot, try to stop it
  if nmcli -t -f NAME,TYPE,DEVICE connection show --active | grep -q '802-11-wireless'; then
    # get any active wifi connection
    name_arg=$(nmcli -t -f NAME,TYPE connection show --active | awk -F: '$2=="802-11-wireless" {print $1; exit}')
  fi

  if [[ -z "$name_arg" ]]; then
    echo "No active hotspot connection found. Nothing to stop."
    exit 0
  fi

  echo "Stopping hotspot connection: $name_arg"
  nmcli connection down "$name_arg" || true
  echo "Deleting connection: $name_arg"
  nmcli connection delete "$name_arg" || true
  echo "Hotspot stopped."
}

status_hotspot() {
  echo "Active Wi-Fi connections (nmcli):"
  nmcli -f NAME,UUID,TYPE,DEVICE,STATE connection show --active | sed -n '1,200p'
  echo
  echo "Nearby Wi‑Fi networks (scan):"
  nmcli device wifi list ifname "${IFACE:-}" | sed -n '1,20p'
  echo
  echo "ARP/neighbors (possible clients):"
  ip neigh show
}

# main
require_nmcli

case "$CMD" in
  start)
    # parse the rest via the function (shift the command)
    parse_args "$@"
    start_hotspot
    ;;
  stop)
    parse_args "$@"
    stop_hotspot
    ;;
  status)
    parse_args "$@"
    status_hotspot
    ;;
  help|""|*)
    print_help
    ;;
esac