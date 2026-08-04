import json
import os
import re
import subprocess
from pathlib import Path
from typing import List

from .models import HotspotConfig, Client, InterfaceInfo
from .runner import CommandError

PS_SCRIPT = Path(__file__).resolve().parent / "assets" / "windows_tethering.ps1"


def _run(args, check=True, timeout=45):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, shell=False)
    if check and p.returncode != 0:
        raise CommandError(p.stderr.strip() or p.stdout.strip() or f"Command failed: {args}")
    return p


def _powershell(script_path: Path, *arguments, check=True):
    if not script_path.exists():
        raise CommandError(f"Missing Windows backend script: {script_path}")
    args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    args.extend(arguments)
    return _run(args, check=check)


def _json_call(action, **params):
    payload = json.dumps(params, ensure_ascii=True)
    result = _powershell(PS_SCRIPT, "-Action", action, "-Json", payload, check=False)
    if result.returncode != 0:
        raise CommandError(result.stderr.strip() or result.stdout.strip() or "Windows tethering backend failed")
    text = result.stdout.strip()
    if not text:
        raise CommandError("Windows tethering backend returned no result")
    try:
        data = json.loads(text.splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise CommandError(f"Invalid Windows backend response: {text}") from exc
    if not data.get("ok", False):
        raise CommandError(data.get("error", "Windows Mobile Hotspot operation failed"))
    return data


def is_admin():
    if os.name != "nt":
        return False
    return _run(["net", "session"], check=False).returncode == 0


def wifi_interfaces() -> List[InterfaceInfo]:
    # Get-NetAdapter is the authoritative Windows adapter inventory.
    ps = _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
               "Get-NetAdapter | Where-Object {$_.NdisPhysicalMedium -eq 'Native 802.11' -or $_.InterfaceDescription -match 'Wi-Fi|Wireless|802.11|WLAN'} | Select-Object Name,Status,InterfaceDescription | ConvertTo-Json -Compress"], check=False)
    result = []
    if ps.returncode == 0 and ps.stdout.strip():
        try:
            rows = json.loads(ps.stdout)
            if isinstance(rows, dict): rows = [rows]
            for row in rows:
                name = str(row.get("Name", "")).strip()
                if name:
                    result.append(InterfaceInfo(name, "wifi", str(row.get("Status", "unknown")).lower(), name))
        except Exception:
            pass
    if result:
        return result
    p = _run(["netsh", "wlan", "show", "interfaces"], check=False)
    for m in re.finditer(r"^\s*(?:Name|Nom)\s*:\s*(.+)$", p.stdout, re.M | re.I):
        name = m.group(1).strip()
        result.append(InterfaceInfo(name, "wifi", "unknown", name))
    return result


def driver_report():
    return _run(["netsh", "wlan", "show", "drivers"], check=False).stdout


def hosted_network_supported():
    return bool(re.search(r"Hosted network supported\s*:\s*Yes", driver_report(), re.I))


def wireless_capabilities():
    return _run(["netsh", "wlan", "show", "wirelesscapabilities"], check=False).stdout


def _native_available():
    if os.name != "nt":
        return False
    try:
        from . import windows_native
        return bool(windows_native.probe().get("available"))
    except Exception:
        return False


def mobile_hotspot_capability():
    try:
        from . import windows_native
        report = windows_native.probe()
        if report.get("available"):
            return report
    except Exception:
        pass
    return _json_call("probe")


def start(config: HotspotConfig):
    config.validate()
    if os.name != "nt":
        raise CommandError("Windows backend can only run on Windows.")

    # Preferred modern Windows Mobile Hotspot / WinRT tethering API.
    try:
        from . import windows_native
        native = windows_native.probe()
        if native.get("available"):
            data = windows_native.start(config.ssid, config.password)
            return f"Windows Mobile Hotspot // {data.get('ssid', config.ssid)} // {data.get('status', 'Success')}"
        native_error = native.get("error", "Windows tethering API unavailable")
    except Exception as exc:
        native_error = str(exc)
    try:
        data = _json_call("start", ssid=config.ssid, password=config.password)
        return data.get("message", f"Windows Mobile Hotspot // {config.ssid}")
    except CommandError as modern_error:
        modern_error = CommandError(f"Native WinRT: {native_error}; PowerShell bridge: {modern_error}")
        # Legacy Hosted Network remains a real fallback for older/special drivers.
        if hosted_network_supported():
            if not is_admin():
                raise PermissionError("Administrator privileges are required for the legacy Hosted Network fallback.")
            _run(["netsh", "wlan", "set", "hostednetwork", "mode=allow", f"ssid={config.ssid}", f"key={config.password}", "keyUsage=temporary"])
            result = _run(["netsh", "wlan", "start", "hostednetwork"], check=False)
            if result.returncode != 0:
                raise CommandError(result.stderr.strip() or result.stdout.strip() or "Unable to start Windows Hosted Network.")
            return f"Windows Hosted Network // {config.ssid}"
        raise CommandError(
            "Windows Mobile Hotspot could not be started. "
            f"Modern backend: {modern_error}. "
            "Open Windows Settings > Network & Internet > Mobile hotspot to verify the feature works on this PC."
        )


def stop():
    if os.name != "nt":
        return
    try:
        from . import windows_native
        if windows_native.probe().get("available"):
            windows_native.stop()
            return
    except Exception:
        pass
    try:
        _json_call("stop")
        return
    except CommandError:
        if hosted_network_supported():
            _run(["netsh", "wlan", "stop", "hostednetwork"], check=False)


def status():
    try:
        from . import windows_native
        if windows_native.probe().get("available"):
            return json.dumps(windows_native.status(), indent=2)
    except Exception:
        pass
    try:
        data = _json_call("status")
        return json.dumps(data, indent=2)
    except CommandError:
        return _run(["netsh", "wlan", "show", "hostednetwork"], check=False).stdout


def _normalize_mac(value: str) -> str:
    return re.sub(r"[^0-9a-f]", "", str(value).lower())


def _arp_neighbors():
    """Return a best-effort Windows IP->MAC/host mapping for tethered clients.

    Windows' tethering client objects expose MAC/host names but do not expose
    the DHCP lease IP directly.  ARP/neighbor data bridges that gap when the
    client has recently exchanged traffic with the host.
    """
    result = {}
    try:
        p = _run(["arp", "-a"], check=False)
        current_ip = None
        for line in p.stdout.splitlines():
            m_ip = re.match(r"\s*Interface:\s*(\d+\.\d+\.\d+\.\d+)", line, re.I)
            if m_ip:
                current_ip = m_ip.group(1)
                continue
            m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+(\w+)", line)
            if m:
                ip, mac, state = m.groups()
                result[_normalize_mac(mac)] = {
                    "ip": ip,
                    "mac": mac.replace("-", ":").upper(),
                    "arp_state": state.upper(),
                    "interface": current_ip or "",
                }
    except Exception:
        pass
    return result


def clients() -> List[Client]:
    """Return live Windows Mobile Hotspot clients, enriched with IP/ARP data."""
    try:
        from . import windows_native
        native = windows_native.probe()
        if native.get("available"):
            tethered = windows_native.clients()
        else:
            data = _json_call("clients")
            tethered = data.get("clients", [])

        arp = _arp_neighbors()
        result = []
        seen = set()

        # The Windows tethering API is the authoritative connected-client list.
        for item in tethered:
            mac = str(item.get("mac", "")).strip()
            key = _normalize_mac(mac)
            match = arp.get(key, {})
            hosts = item.get("hosts", []) or []
            host = ", ".join(str(x) for x in hosts if str(x).strip()) or "UNKNOWN DEVICE"
            state = match.get("arp_state", "ONLINE")
            result.append(Client(
                match.get("ip", "IP PENDING"),
                match.get("mac", mac or match.get("mac", "MAC UNKNOWN")),
                f"{state} // {host}",
            ))
            if key:
                seen.add(key)

        # If Windows reports a client count but its client collection is not
        # populated yet, use recent ARP neighbors as a useful live fallback.
        reported_count = int(native.get("client_count", 0) or 0) if native.get("available") else 0
        for key, item in arp.items():
            if key in seen:
                continue
            # Mobile Hotspot normally uses the 192.168.137.0/24 subnet.
            if item["ip"].startswith("192.168.137."):
                result.append(Client(item["ip"], item["mac"], item["arp_state"]))
                seen.add(key)

        return result
    except Exception:
        # Last-resort ARP display. This is useful even if the tethering API
        # temporarily cannot enumerate clients.
        arp = _arp_neighbors()
        return [
            Client(v["ip"], v["mac"], v["arp_state"])
            for v in arp.values()
            if v["ip"].startswith("192.168.137.")
        ]

