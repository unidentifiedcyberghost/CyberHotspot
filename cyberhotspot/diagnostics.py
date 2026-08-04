import os
import platform
from .models import DoctorReport
from .runner import which


def doctor() -> DoctorReport:
    report = DoctorReport()
    report.checks.append(f"OS: {platform.platform()}")
    report.checks.append(f"Python: {platform.python_version()}")

    if os.name == "nt":
        from .windows_backend import wifi_interfaces, driver_report, mobile_hotspot_capability, hosted_network_supported
        try:
            adapters = wifi_interfaces()
            if adapters:
                for item in adapters:
                    report.checks.append(f"Wi-Fi: {item.name} state={item.state}")
            else:
                report.errors.append("Windows Wi-Fi adapter: not detected")
            try:
                modern = mobile_hotspot_capability()
                report.checks.append("Windows Mobile Hotspot API: available")
                report.checks.append(f"Mobile Hotspot state: {modern.get('state', 'Unknown')}")
            except Exception as exc:
                report.errors.append(f"Windows Mobile Hotspot API: unavailable ({exc})")
                if hosted_network_supported():
                    report.warnings.append("Legacy Hosted Network is available as a fallback.")
                else:
                    report.warnings.append("Legacy Hosted Network is also unavailable.")
            drivers = driver_report()
            if drivers:
                report.checks.append("Windows WLAN driver information: available")
        except Exception as exc:
            report.errors.append(f"Windows network inspection failed: {exc}")
        if which("qrencode"):
            report.checks.append("qrencode: available")
        else:
            report.warnings.append("qrencode: not installed; Python qrcode can be used for PNG output.")
        return report

    for command in ("nmcli", "ip", "iw"):
        if which(command):
            report.checks.append(f"{command}: available")
        else:
            report.errors.append(f"{command}: missing")

    try:
        from .network import wireless_interfaces, ap_capable
        wifi = wireless_interfaces()
        if wifi:
            for item in wifi:
                capable = ap_capable(item.name)
                item.supports_ap = capable
                report.checks.append(f"Wi-Fi: {item.name} state={item.state} AP-capable={capable}")
            if not any(x.supports_ap for x in wifi):
                report.warnings.append("No detected Wi-Fi interface reported AP support.")
        else:
            report.warnings.append("No Wi-Fi interface is visible to NetworkManager.")
    except Exception as exc:
        report.errors.append(f"Interface inspection failed: {exc}")

    if os.path.exists("/.dockerenv") or os.path.exists("/run/systemd/container"):
        report.warnings.append("Container/virtualized environment detected.")

    if which("hostapd"):
        report.checks.append("hostapd: available (optional fallback tooling)")
    else:
        report.warnings.append("hostapd: not installed (not required for NetworkManager mode).")

    if which("qrencode"):
        report.checks.append("qrencode: available")
    else:
        report.warnings.append("qrencode: not installed; Python qrcode can be used for PNG output.")
    return report
