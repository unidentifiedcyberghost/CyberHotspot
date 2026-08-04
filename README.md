<img width="1918" height="1078" alt="observability" src="https://github.com/user-attachments/assets/cf08fdd0-872e-410b-8f55-bf492bc654c1" />
<img width="815" height="170" alt="ascii-art-text" src="https://github.com/user-attachments/assets/a13979eb-fc13-46bd-841b-a7c30a62689f" />
<img width="1362" height="770" alt="CyberHotspot-v2 7 0-Compact-HUD-Live-Clients = stable na din" src="https://github.com/user-attachments/assets/14ac14ff-b8a1-4c0a-b76b-115462524f45" />


<img width="1371" height="770" alt="CyberHotspot-v2 8 0-Local-Observability-HUD installing python" src="https://github.com/user-attachments/assets/322a4881-9d89-475d-a39c-cd1035713576" />

<img width="1462" height="776" alt="sampe tree" src="https://github.com/user-attachments/assets/5922cb91-1405-486f-8ebf-c27d0ff1831d" />

<img width="1918" height="1078" alt="observability" src="https://github.com/user-attachments/assets/51557f93-6189-459f-9357-1d0482423407" />


# CyberHotspot

**CyberHotspot v2.7.0 — Compact Cross-Platform**

A practical Wi-Fi hotspot manager with a PyQt5 futuristic HUD, terminal CLI, Linux NetworkManager backend, and Windows Mobile Hotspot / Tethering backend.

> CyberHotspot uses the capabilities actually exposed by the OS. It does not bypass Wi-Fi driver, hardware, virtualization, or OS limitations.

## Windows

Open **PowerShell as Administrator**:

```powershell
cd C:\path\to\CyberHotspot
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[qr]"
cyberhotspot capabilities
netsh wlan show drivers
cyberhotspot-gui
```

Legacy Hosted Network support is optional. Modern Windows Mobile Hotspot control uses the Windows tethering API and does not require `Hosted network supported : Yes`.


Start:

```powershell
cyberhotspot start --ssid CyberHotspot --password pinoyunknown
```

Stop:

```powershell
cyberhotspot stop
```

Status:

```powershell
cyberhotspot status
```

If Hosted Network is unsupported, Windows Mobile Hotspot may still be available through Windows Settings. CyberHotspot reports this separately because the modern Mobile Hotspot API is not the same interface as legacy `netsh`.

## Linux

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip network-manager iw rfkill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[qr]"
cyberhotspot capabilities
cyberhotspot-gui
```

Start:

```bash
sudo cyberhotspot start --ssid CyberHotspot --password pinoyunknown --shared
```

## HUD

The GUI uses a futuristic HUD control-deck style inspired by the supplied reference:

- cyan primary borders
- magenta/pink highlights
- yellow status accents
- angular panels
- telemetry blocks
- capability dashboard
- live clients
- Windows/Linux backend status
- branded footer

## VirtualBox

A VirtualBox Linux guest normally sees virtual Ethernet, not the host's physical Wi-Fi radio. If the guest only has `enp0s3`, it cannot create a Wi-Fi AP through `nmcli`.

For a guest hotspot, pass through a USB Wi-Fi adapter supporting AP mode. Otherwise run CyberHotspot on the Windows host.

## Diagnostics

```bash
cyberhotspot capabilities
cyberhotspot hardware
cyberhotspot doctor
```

## Source protection

Normal Python source cannot be made impossible to copy while remaining a normal Python application. Treat obfuscation/packaging as distribution hardening, not a security boundary. Never hard-code sensitive credentials or keys.

## License

MIT


## Windows built-in Mobile Hotspot

CyberHotspot v2.6 uses the supported Windows `NetworkOperatorTetheringManager` API for the built-in Mobile Hotspot. The legacy `netsh` Hosted Network feature is not required. Windows requires the `wiFiControl` device capability for programmatic tethering, so the deployable Windows build is an MSIX package.

Build the Windows package from PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\packaging\windows\build-msix.ps1
```

Microsoft documents `CreateFromConnectionProfile`, `ConfigureAccessPointAsync`, and `StartTetheringAsync` for this functionality and requires the `wiFiControl` capability.


## v2.7 Compact HUD / Live Client Monitor

The v2.7 GUI is intentionally compact so future network modules can be added without redesigning the control deck.

- Compact SSID/password controls.
- Collapsible Wi-Fi navigation settings.
- Smaller cyberpunk HUD network-control buttons.
- Persistent `SYSTEM ONLINE` and `HOTSPOT ACTIVE` indicators.
- Connected Clients panel with live count.
- Windows tethering client MAC/hostname details.
- Best-effort IP enrichment from Windows ARP/neighbor data.
- `DETAILS PENDING` row when Windows reports a client before its detailed enumeration arrives.
- System Telemetry is the larger panel and remains scrollable for detailed logs.
- Telemetry and client information refresh automatically every two seconds.
- The Windows tethering API remains the authoritative source for the connected-client count; ARP is only used to enrich client details.

The GUI does not invent a device name or IP address when Windows does not expose it. Unknown values are displayed explicitly as `UNKNOWN`, `IP PENDING`, or `DETAILS PENDING`.

