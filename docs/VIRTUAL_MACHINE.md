# Virtual Machine Tips — CyberHotspot

Running an actual Wi‑Fi access point requires control of the physical Wi‑Fi radio. Virtual machines commonly virtualize networking and do not expose the host radio by default.

Recommended options
1. USB Wi‑Fi adapter + passthrough (recommended)
   - Attach a USB Wi‑Fi dongle to host.
   - In VirtualBox / VMware, enable USB passthrough for the VM to own the USB device.
   - Inside the VM, the Wi‑Fi adapter appears as a physical device; NetworkManager can manage it.

2. Host manages AP, VM uses LAN
   - Create a hotspot on the host machine and bridge/share its network with the VM.
   - The VM will use the host’s network but not control AP features.

3. USB to Ethernet adapters and dedicated hardware
   - For production, use an external router or hardware AP.

Troubleshooting
- If no wireless interface appears in the VM: verify USB device is passed through (VirtualBox: Devices → USB → select).
- On VirtualBox, install Extension Pack for USB 2.0/3.0 passthrough.
- Use `nmcli device` and `iw dev` to verify device presence and AP capability (AP == "AP" in supported modes).