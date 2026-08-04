
from dataclasses import dataclass, field
from typing import List
import os, re, platform as pyplatform
from .runner import run, which
from .network import interfaces

@dataclass
class CapabilityReport:
    platform: str
    virtualization: str
    network_manager: bool
    nmcli: bool
    wifi_interfaces: List[str]=field(default_factory=list)
    ethernet_interfaces: List[str]=field(default_factory=list)
    ap_interfaces: List[str]=field(default_factory=list)
    rfkill_blocked: bool=False
    rfkill_hard_blocked: bool=False
    hostapd: bool=False
    dnsmasq: bool=False
    nftables: bool=False
    iw: bool=False
    usb_wifi_hint: bool=False
    regulatory_domain: str="unknown"
    driver_hints: List[str]=field(default_factory=list)
    backends: List[str]=field(default_factory=list)
    selected_backend: str="none"
    ready: bool=False
    reasons: List[str]=field(default_factory=list)
    recommendations: List[str]=field(default_factory=list)

def _cmd(args):
    return run(args,check=False).stdout.strip() if which(args[0]) else ""

def _virt():
    if os.name=="nt": return "physical-windows"
    if which("systemd-detect-virt"):
        v=_cmd(["systemd-detect-virt"])
        if v and v!="none": return v
    if os.path.exists("/.dockerenv"): return "docker"
    try:
        if "hypervisor" in open("/proc/cpuinfo",errors="ignore").read().lower(): return "virtual-machine"
    except OSError: pass
    return "physical-linux"

def _windows_scan():
    from .windows_backend import wifi_interfaces, hosted_network_supported, driver_report, wireless_capabilities, mobile_hotspot_capability
    r=CapabilityReport(f"Windows {pyplatform.release()}",_virt(),False,False)
    r.wifi_interfaces=[x.name for x in wifi_interfaces()]
    drivers=driver_report()
    if drivers:
        m=re.search(r"Hosted network supported\s*:\s*(Yes|No)",drivers,re.I)
        if m: r.driver_hints.append("Legacy Hosted Network: "+m.group(1))
    if wireless_capabilities(): r.driver_hints.append("Windows wireless capabilities detected")

    try:
        modern=mobile_hotspot_capability()
        r.backends.append("windows-mobile-hotspot")
        r.selected_backend="windows-mobile-hotspot"
        r.ap_interfaces=r.wifi_interfaces[:]
        r.ready=True
        r.driver_hints.append("Modern Windows Mobile Hotspot / WinRT tethering API: available")
        r.driver_hints.append("Tethering state: "+str(modern.get("state","Unknown")))
        return r
    except Exception as exc:
        r.driver_hints.append("Modern Windows Mobile Hotspot API: unavailable")
        r.reasons.append(str(exc))

    if r.wifi_interfaces and hosted_network_supported():
        r.ap_interfaces=r.wifi_interfaces[:]
        r.backends.append("windows-hostednetwork")
        r.selected_backend="windows-hostednetwork"
        r.ready=True
    elif r.wifi_interfaces:
        r.recommendations.append("Windows Mobile Hotspot API could not be accessed. Open Settings > Network & Internet > Mobile hotspot to verify the Windows feature.")
    else:
        r.reasons.append("No Windows Wi-Fi adapter was detected.")
        r.recommendations.append("Enable the Wi-Fi adapter and verify it in Windows Network Connections.")
    return r

def _linux_scan():
    r=CapabilityReport(pyplatform.system(),_virt(),bool(which("NetworkManager")) or os.path.exists("/run/NetworkManager"),bool(which("nmcli")),iw=bool(which("iw")),hostapd=bool(which("hostapd")),dnsmasq=bool(which("dnsmasq")),nftables=bool(which("nft")))
    try:
        for i in interfaces():
            if i.kind in ("wifi","802-11-wireless"): r.wifi_interfaces.append(i.name)
            elif i.kind in ("ethernet","802-3-ethernet"): r.ethernet_interfaces.append(i.name)
    except Exception as exc: r.reasons.append(f"Interface inspection failed: {exc}")
    if r.iw:
        text=_cmd(["iw","list"])
        if re.search(r"(?m)^\s*\*?\s*AP\s*$",text): r.ap_interfaces=r.wifi_interfaces[:]
        m=re.search(r"country\s+([A-Z]{2})",_cmd(["iw","reg","get"]))
        if m: r.regulatory_domain=m.group(1)
    if which("rfkill"):
        text=_cmd(["rfkill","list"]); r.rfkill_blocked=bool(re.search(r"Soft blocked:\s+yes",text,re.I)); r.rfkill_hard_blocked=bool(re.search(r"Hard blocked:\s+yes",text,re.I))
    if r.network_manager and r.nmcli: r.backends.append("networkmanager")
    if r.hostapd: r.backends.append("hostapd")
    if r.hostapd and r.dnsmasq and r.nftables: r.backends.append("hostapd+nftables")
    if r.rfkill_hard_blocked: r.reasons.append("Wi-Fi is hard-blocked.")
    elif r.rfkill_blocked: r.reasons.append("Wi-Fi is soft-blocked by rfkill."); r.recommendations.append("Run `sudo rfkill unblock wifi`.")
    if not r.wifi_interfaces:
        r.reasons.append("No Wi-Fi interface is exposed to Linux.")
        if r.virtualization not in ("physical-linux","physical"): r.recommendations.append("A VM normally exposes virtual Ethernet only. Use USB Wi-Fi passthrough or run CyberHotspot on the host.")
    elif not r.ap_interfaces:
        r.reasons.append("Wi-Fi exists, but AP mode was not detected."); r.recommendations.append("Run `iw list` and verify AP support.")
    if not r.backends: r.recommendations.append("Install NetworkManager or hostapd/dnsmasq/nftables as appropriate.")
    if r.ap_interfaces and not r.rfkill_blocked and not r.rfkill_hard_blocked:
        if "networkmanager" in r.backends: r.selected_backend="networkmanager"
        elif "hostapd+nftables" in r.backends: r.selected_backend="hostapd+nftables"
        elif "hostapd" in r.backends: r.selected_backend="hostapd"
        r.ready=r.selected_backend!="none"
    return r

def scan_capabilities():
    return _windows_scan() if os.name=="nt" else _linux_scan()
