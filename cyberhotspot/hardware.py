import os
import platform
import re
from dataclasses import dataclass
from typing import List, Optional

from .runner import run, which
from .network import interfaces


@dataclass
class HardwareReport:
    vm_detected: bool
    vm_vendor: str
    wifi_present: bool
    wifi_interfaces: List[str]
    ap_capable: bool
    ap_interfaces: List[str]
    ethernet_interfaces: List[str]
    warnings: List[str]


def _virtualization() -> str:
    if which("systemd-detect-virt"):
        result = run(["systemd-detect-virt"], check=False)
        value = result.stdout.strip()
        if value and value != "none":
            return value

    if Path("/.dockerenv").exists():
        return "docker"

    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(errors="ignore").lower()
        if "hypervisor" in cpuinfo:
            if "virtualbox" in cpuinfo:
                return "virtualbox"
            if "vmware" in cpuinfo:
                return "vmware"
            if "kvm" in cpuinfo:
                return "kvm"
            if "qemu" in cpuinfo:
                return "qemu"
            return "virtual-machine"
    except OSError:
        pass
    return ""


def _ap_capable(iface: str) -> bool:
    if not which("iw"):
        return False
    result = run(["iw", "list"], check=False)
    return bool(re.search(r"(?m)^\s*\*?\s*AP\s*$", result.stdout))


def inspect_hardware() -> HardwareReport:
    warnings: List[str] = []
    vm = _virtualization()

    wifi = []
    ethernet = []
    try:
        for item in interfaces():
            if item.kind in ("wifi", "802-11-wireless"):
                wifi.append(item.name)
            elif item.kind in ("ethernet", "802-3-ethernet"):
                ethernet.append(item.name)
    except Exception as exc:
        warnings.append(f"Network interface inspection failed: {exc}")

    ap_ifaces = [name for name in wifi if _ap_capable(name)]

    if not wifi:
        warnings.append(
            "No Wi-Fi interface is visible. A virtual Ethernet adapter cannot create a physical Wi-Fi AP."
        )
    elif not ap_ifaces:
        warnings.append(
            "Wi-Fi detected, but AP mode was not detected. Check driver/firmware support with `iw list`."
        )

    if vm and not wifi:
        warnings.append(
            f"Virtual environment detected ({vm}). Attach a USB Wi-Fi adapter with AP support "
            "to the guest or run the hotspot on the host."
        )

    return HardwareReport(
        vm_detected=bool(vm),
        vm_vendor=vm or "physical",
        wifi_present=bool(wifi),
        wifi_interfaces=wifi,
        ap_capable=bool(ap_ifaces),
        ap_interfaces=ap_ifaces,
        ethernet_interfaces=ethernet,
        warnings=warnings,
    )


# Import kept here to avoid changing the public hardware API.
from pathlib import Path
