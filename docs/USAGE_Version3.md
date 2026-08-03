# Usage Guide — CyberHotspot

CLI (Recommended: uses nmcli)
- Start hotspot:
  sudo cyberhotspot-cli start --ssid "CyberNet" --passwd "SecretPass123" [--ifname wlan0] [--shared]
- Stop hotspot:
  sudo cyberhotspot-cli stop [--con <connection-name>]
- Status:
  cyberhotspot-cli status
- Generate a QR (for phones):
  cyberhotspot-cli qr --ssid "CyberNet" --passwd "SecretPass123" --out qrcode.png
- List clients:
  cyberhotspot-cli clients

Bash wrapper (fallback)
- scripts/cyberhotspot.sh start --ssid "CyberNet" --passwd "SecretPass"
- scripts/cyberhotspot.sh stop
- scripts/cyberhotspot.sh status

GUI
- Launch:
  python3 -m cyberhotspot.gui
  or run: cyberhotspot-gui (after install)
- Actions:
  - Enter SSID, password, optional interface; press Start.
  - Use "Show QR" to display device-join QR code.
  - Use Stop to end the hotspot; Client list shows connected IPs/mac (best-effort).

Hostapd fallback (advanced)
- The repository includes a hostapd config generator (backend.generate_hostapd_conf).
- To use hostapd fallback:
  - Generate hostapd.conf
  - Run hostapd as root: sudo hostapd /path/to/hostapd.conf
  - Configure dnsmasq for DHCP/DNS and set ip_forwarding + NAT (see TROUBLESHOOTING.md)

Permissions
- CLI hotspot start/stop operations require root privileges.
- GUI will display warnings if not run with permissions; prefer launching GUI with sudo or configure policykit if needed.

Troubleshooting quick checks
- Verify interface supports AP mode:
  iw list | grep -A 10 "Supported interface modes"
- Check NetworkManager logs:
  sudo journalctl -u NetworkManager -e
- If devices don't see SSID, try different channel or verify regulatory domain.
