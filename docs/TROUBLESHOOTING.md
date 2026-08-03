# Troubleshooting

Common issues and fixes

1. nmcli reports an error / hotspot fails to start
- Run: nmcli device status
- Inspect logs: sudo journalctl -u NetworkManager -e
- Check driver support: iw list | grep -A 10 "Supported interface modes"

2. Devices can't connect or get IP
- Ensure dnsmasq or NetworkManager sharing mode is configured.
- Check ip_forward: cat /proc/sys/net/ipv4/ip_forward
- Inspect iptables/nftables for NAT rules.

3. Hostapd fallback issues
- Run hostapd with increased verbosity: sudo hostapd -dd /path/to/hostapd.conf
- Check driver and country_code settings.

4. Virtual machine: no Wi‑Fi device
- Use USB passthrough for a Wi‑Fi dongle.

Logging
- GUI logs are printed to console when launching via python3 -m cyberhotspot.gui
- Increase verbosity in CLI by running functions directly (for developers)

If you cannot resolve, open an issue with:
- Output of: nmcli -t -f all connection show --active
- Output of: iw list
- Journal logs: sudo journalctl -u NetworkManager --since "10 minutes ago"